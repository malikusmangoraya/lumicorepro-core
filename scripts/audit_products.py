#!/usr/bin/env python3
"""Sellability audit for the curated set in `products/`.

Every check is deterministic and evidence-based: it reads real files from disk
and reports PASS / FAIL / WARN with the exact path (or line) that proves it.
Nothing is inferred from a filename alone unless the file is actually opened.

Usage:
    python scripts/audit_products.py                 # human-readable report
    python scripts/audit_products.py --json          # machine-readable
    python scripts/audit_products.py --only apex     # one product
    python scripts/audit_products.py --write-reports # products/AUDIT_*.{json,md}

Exit code is 1 when any product has a FAIL, so it can gate CI.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

# Windows consoles default to cp1252 and blow up on the box-drawing/markdown
# characters used in the report. Force UTF-8 once, before anything prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable
        pass
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Iterable, Optional

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"

# Text that must never ship in a product a stranger is about to pay for.
# (pattern, label, case_sensitive). TODO/FIXME/XXX are matched case-sensitively
# because they are convention markers: a case-insensitive \bTODO\b flags ordinary
# prose and non-English locales (Spanish "todo" = "all") as unfinished work.
PLACEHOLDER_PATTERNS = [
    (r"\blorem ipsum\b", "lorem ipsum filler text", False),
    (r"\bTODO\b", "TODO marker", True),
    (r"\bFIXME\b", "FIXME marker", True),
    (r"\byour[-_ ]?(api[-_ ]?key|secret|token)\b", "placeholder secret wording", False),
    (r"\bcoming soon\b", "unfinished 'coming soon' copy", False),
    (r"\bXXX\b", "XXX marker", True),
    (r"\bexample\.com\b", "example.com placeholder domain", False),
    (r"\bchangeme\b", "changeme placeholder", False),
]

# Real private-key material or provider secrets committed to the tree.
SECRET_PATTERNS = [
    (r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", "private key block"),
    (r"\bsk_live_[0-9a-zA-Z]{20,}", "Stripe live secret key"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key id"),
    (r"\bghp_[0-9A-Za-z]{30,}", "GitHub personal access token"),
    (r"\bxox[baprs]-[0-9A-Za-z-]{10,}", "Slack token"),
    (r"AIza[0-9A-Za-z_\-]{35}", "Google API key"),
]

# Dependency ranges that cannot resolve to a real published package.
BROKEN_RANGES = {
    "sequelize": (r"^\^?1\.", "sequelize ^1.x does not exist; the real line is 6.x"),
}

AUTH_ROUTE_HINTS = ("auth.routes.js", "authRoutes.js", "auth.routes.ts")
SCANNED_EXT = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".yml", ".yaml",
               ".sql", ".html", ".css", ".sh", ".env", ".example", ""}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".next",
             "screenshots", ".artifacts", ".history"}


# --------------------------------------------------------------------------- #
# Finding plumbing
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    check: str
    category: str
    status: str
    detail: str
    evidence: Optional[str] = None


@dataclass
class ProductReport:
    name: str
    path: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, check, category, status, detail, evidence=None):
        self.findings.append(Finding(check, category, status, detail, evidence))

    @property
    def fails(self):
        return [f for f in self.findings if f.status == FAIL]

    @property
    def warns(self):
        return [f for f in self.findings if f.status == WARN]

    @property
    def score(self):
        """PASS-weighted score out of 100; WARN earns half credit."""
        total = len(self.findings) * 2
        got = sum(2 if f.status == PASS else 1 if f.status == WARN else 0
                  for f in self.findings)
        return round(100 * got / total) if total else 0

    @property
    def sellable(self):
        return not self.fails


def ok(rep, check, cat, detail, evidence=None):
    rep.add(check, cat, PASS, detail, evidence)


def bad(rep, check, cat, detail, evidence=None):
    rep.add(check, cat, FAIL, detail, evidence)


def warn(rep, check, cat, detail, evidence=None):
    rep.add(check, cat, WARN, detail, evidence)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def read(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except (OSError, UnicodeDecodeError):
        return ""


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def walk_files(root: Path, exts: Optional[Iterable[str]] = None) -> Iterable[Path]:
    exts = set(exts) if exts else SCANNED_EXT
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            yield p


def grep(root: Path, pattern: str, flags=0) -> list[tuple[Path, int, str]]:
    """Return (path, lineno, line) for every regex match under root."""
    rx = re.compile(pattern, flags)
    hits = []
    for p in walk_files(root):
        for i, line in enumerate(read(p).splitlines(), 1):
            if rx.search(line):
                hits.append((p, i, line.strip()[:160]))
    return hits


def first(root: Path, *names) -> Optional[Path]:
    for n in names:
        p = root / n
        if p.is_file():
            return p
    return None


# --------------------------------------------------------------------------- #
# Individual check groups
# --------------------------------------------------------------------------- #
def check_security(rep: ProductReport, p: Path):
    cat = "Security"

    # Hardcoded credentials that are seeded on module import.
    cred = grep(p, r"Password123|12345678|admin@.*\.com['\"]\s*,?\s*$|password\s*[:=]\s*['\"][^'\"]{6,}['\"]")
    hard = [h for h in cred if "seed" not in h[0].name.lower() and "test" not in h[0].name.lower()]
    hard = [h for h in hard if not h[0].name.endswith(".md")]
    if hard:
        f, ln, txt = hard[0]
        rel = f.relative_to(p).as_posix()
        bad(rep, "no-hardcoded-credentials", cat,
            f"{len(hard)} hardcoded credential literal(s) in shipped runtime code",
            f"{rel}:{ln}  {txt}")
    else:
        ok(rep, "no-hardcoded-credentials", cat, "no hardcoded password literals in runtime code")

    # Real key material.
    leaked = []
    for rx, label in SECRET_PATTERNS:
        leaked += [(h[0], h[1], label) for h in grep(p, rx)]
    if leaked:
        f, ln, label = leaked[0]
        bad(rep, "no-committed-secrets", cat,
            f"{len(leaked)} committed secret(s): {label}",
            f"{f.relative_to(p).as_posix()}:{ln}")
    else:
        ok(rep, "no-committed-secrets", cat, "no private keys or provider tokens in the tree")

    # .env must never be shipped; only .env.example.
    real_env = [x.name for x in p.glob(".env*") if ".example" not in x.name and ".sample" not in x.name]
    if real_env:
        bad(rep, "no-env-file-shipped", cat, f"real env file(s) present: {', '.join(real_env)}")
    else:
        ok(rep, "no-env-file-shipped", cat, "no live .env file in the deliverable")

    # Backend security middleware.
    server = first(p, "backend/server.js", "backend/src/server.js")
    if server:
        s = read(server)
        missing = [m for m in ("helmet", "cors", "rateLimit") if m not in s]
        if missing:
            warn(rep, "backend-hardening", cat,
                 f"server.js missing middleware reference(s): {', '.join(missing)}",
                 server.relative_to(p).as_posix())
        else:
            ok(rep, "backend-hardening", cat, "helmet + cors + rate limiting wired in server.js")

    gi = p / ".gitignore"
    if gi.is_file():
        g = read(gi)
        need = [x for x in (".env", "node_modules") if x not in g]
        if need:
            bad(rep, "gitignore-coverage", cat, f".gitignore missing: {', '.join(need)}")
        else:
            ok(rep, "gitignore-coverage", cat, ".gitignore covers .env and node_modules")
    else:
        bad(rep, "gitignore-coverage", cat, "no .gitignore")


def check_dependencies(rep: ProductReport, p: Path):
    cat = "Dependencies"
    for rel, label in (("frontend/package.json", "frontend"), ("backend/package.json", "backend")):
        pj = p / rel
        if not pj.is_file():
            bad(rep, f"{label}-manifest", cat, f"missing {rel}")
            continue
        data = load_json(pj)
        if data is None:
            bad(rep, f"{label}-manifest", cat, f"{rel} is not valid JSON")
            continue
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        broken = []
        for name, (rx, why) in BROKEN_RANGES.items():
            if name in deps and re.match(rx, deps[name]):
                broken.append(f"{name}={deps[name]} ({why})")
        if broken:
            bad(rep, f"{label}-version-pins", cat, "; ".join(broken), rel)
        else:
            ok(rep, f"{label}-version-pins", cat, f"{len(deps)} dependency ranges resolve")

        lock = (p / rel).with_name("package-lock.json")
        if lock.is_file():
            ok(rep, f"{label}-lockfile", cat, "package-lock.json present (npm ci reproducible)")
        else:
            warn(rep, f"{label}-lockfile", cat, "no package-lock.json — CI cannot use npm ci", rel)

        scripts = data.get("scripts", {})
        if label == "frontend" and "build" not in scripts:
            bad(rep, "frontend-build-script", cat, "frontend has no build script", rel)


def check_frontend(rep: ProductReport, p: Path):
    cat = "Frontend / UI-UX"
    fe = p / "frontend"
    if not fe.is_dir():
        bad(rep, "frontend-present", cat, "no frontend/ directory")
        return

    src = fe / "src"
    pages = src / "pages"
    names = {q.stem.lower() for q in pages.glob("*.jsx")} if pages.is_dir() else set()
    names |= {q.stem.lower() for q in pages.glob("*.tsx")} if pages.is_dir() else set()

    if not names:
        bad(rep, "frontend-pages", cat, "no page components found under frontend/src/pages")
    else:
        ok(rep, "frontend-pages", cat, f"{len(names)} page components: {', '.join(sorted(names))}")

    login = {"login", "signin", "log-in", "sign-in"} & names
    signup = {"register", "signup", "sign-up", "sign-up"}
    signup = (signup | {"register"}) & names
    if login:
        ok(rep, "login-page", cat, f"login page: {sorted(login)[0]}.jsx")
    else:
        bad(rep, "login-page", cat, "no login page component")

    if signup:
        ok(rep, "signup-page", cat, f"signup page: {sorted(signup)[0]}.jsx")
    else:
        bad(rep, "signup-page", cat, "no signup/register page component")

    # Auth screens actually wired into the router.
    router = first(fe, "src/App.jsx", "src/main.jsx", "src/routes/index.jsx")
    if router:
        r = read(router)
        wired = [p_ for p_ in ("Login", "Register", "Signup") if re.search(rf"\b{p_}\b", r)]
        if wired:
            ok(rep, "auth-routed", cat, f"auth screens routed in {router.name}: {', '.join(wired)}")
        elif {"login", "signin", "register", "signup"} & names:
            bad(rep, "auth-routed", cat,
                f"login/signup pages exist but no auth screen is routed in {router.name} "
                f"— the buyer cannot sign in from the UI",
                router.relative_to(p).as_posix())
        else:
            warn(rep, "auth-routed", cat, f"no auth screens to route in {router.name}")

    for label, rel in (("privacy-page", "frontend/src/pages/Privacy.jsx"),
                       ("terms-page", "frontend/src/pages/Terms.jsx")):
        if (p / rel).is_file():
            ok(rep, label, cat, rel)
        else:
            warn(rep, label, cat, f"no {rel}")

    # Design system.
    tokens = [q for q in (fe / "design-tokens.json", p / "DESIGN-TOKENS.md") if q.is_file()]
    if tokens:
        ok(rep, "design-tokens", cat, f"design tokens present ({tokens[0].name})")
    else:
        warn(rep, "design-tokens", cat, "no design-token file")

    css = list((p / "frontend/src").rglob("*.css"))
    if any("prefers-reduced-motion" in read(c) for c in css):
        ok(rep, "reduced-motion", cat, "honours prefers-reduced-motion")
    else:
        warn(rep, "reduced-motion", cat, "no prefers-reduced-motion handling found in any stylesheet")

    if any("tailwind" in read(c).lower() or "tailwind" in read(fe / "package.json").lower() for c in css) \
            or (fe / "tailwind.config.js").is_file() or (fe / "tailwind.config.cjs").is_file():
        ok(rep, "layout-system", cat, "utility layout system (Tailwind) configured")
    else:
        warn(rep, "layout-system", cat, "no recognisable CSS layout system")


def check_i18n(rep: ProductReport, p: Path):
    cat = "Internationalisation"
    loc = p / "frontend/src/i18n/locales"
    files = sorted(x.stem for x in loc.glob("*.json")) if loc.is_dir() else []
    if len(files) >= 5:
        ok(rep, "i18n-coverage", cat, f"{len(files)} locales: {', '.join(files)}")
    elif files:
        warn(rep, "i18n-coverage", cat, f"only {len(files)} locale(s): {', '.join(files)}")
    else:
        bad(rep, "i18n-coverage", cat, "no i18n locale bundles")

    rtl = {"ar", "he", "fa", "ur"}
    if rtl & set(files):
        have = sorted(rtl & set(files))
        css = list((p / "frontend/src").rglob("*.css"))
        hit = [c for c in css if re.search(r"\bdir\s*=|\[dir=['\"]rtl|:root:dir\(rtl\)", read(c))]
        if hit:
            ok(rep, "rtl-support", cat, f"RTL styles for {', '.join(have)} in {hit[0].name}")
        else:
            warn(rep, "rtl-support", cat,
                 f"RTL languages shipped ({', '.join(have)}) but no [dir=rtl] CSS found")

    money = grep(p / "frontend/src", r"(USD|EUR|GBP|AED|PKR|INR|Intl\.NumberFormat)", re.I)
    if money:
        ok(rep, "currency-localisation", cat, f"{len(money)} currency/locale-formatting reference(s)")
    else:
        warn(rep, "currency-localisation", cat, "no currency or locale number formatting found")

    _check_locale_content(rep, p, cat, loc, files)


def _load_locale(path: Path) -> dict:
    """Read a locale bundle and flatten it to {dotted.key: value}."""
    def walk(node, prefix=""):
        if isinstance(node, dict):
            for key, value in node.items():
                yield from walk(value, f"{prefix}.{key}" if prefix else key)
        else:
            yield prefix, node

    return dict(walk(json.loads(path.read_bytes().decode("utf-8"))))


def _check_locale_content(rep: ProductReport, p: Path, cat: str, loc: Path, files: list[str]):
    """Prove the locales are actually translated, not English with extra files.

    A locale count says nothing about content. Shipping 13 locale files whose
    values are still English means an Arabic, Urdu or Japanese visitor sees
    English buttons inside a translated page — which is what this catches.
    """
    if "en" not in files:
        return
    try:
        english = _load_locale(loc / "en.json")
    except (OSError, ValueError) as exc:
        bad(rep, "i18n-readable", cat, f"en.json unreadable: {exc}")
        return

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from i18n_locale_pack import needs_translation
    except ImportError as exc:  # pragma: no cover - pack must ship with the auditor
        bad(rep, "i18n-pack", cat, f"translation pack unavailable: {exc}")
        return

    leftovers: dict[str, int] = {}
    key_gaps: dict[str, int] = {}
    for code in files:
        if code == "en":
            continue
        try:
            other = _load_locale(loc / f"{code}.json")
        except (OSError, ValueError) as exc:
            bad(rep, f"i18n-readable-{code}", cat, f"{code}.json unreadable: {exc}")
            continue
        key_gaps[code] = len(set(english) ^ set(other))
        count = 0
        for key, value in other.items():
            source = english.get(key)
            if source is None or not isinstance(value, str):
                continue
            text = value.strip()
            if not text or text != str(source).strip():
                continue
            # Proper nouns, addresses, and reviewed cognates (French "Contact",
            # Spanish "No") are identical on purpose, not untranslated.
            if needs_translation(code, text):
                count += 1
        leftovers[code] = count

    untranslated = sum(leftovers.values())
    worst = sorted(leftovers.items(), key=lambda kv: -kv[1])[:4]
    if untranslated == 0:
        ok(rep, "i18n-translated", cat,
           f"all {len(files) - 1} non-English locales fully translated "
           f"({len(english)} keys each, 0 English leftovers)")
    elif untranslated <= 20:
        warn(rep, "i18n-translated", cat,
             f"{untranslated} English leftover value(s); worst: "
             + ", ".join(f"{c}={n}" for c, n in worst))
    else:
        bad(rep, "i18n-translated", cat,
            f"{untranslated} English value(s) left untranslated; worst: "
            + ", ".join(f"{c}={n}" for c, n in worst)
            + " — run scripts/i18n_fill_locales.py")

    gap_langs = {c: n for c, n in key_gaps.items() if n}
    if not gap_langs:
        ok(rep, "i18n-key-parity", cat,
           f"every locale carries exactly the {len(english)} English keys")
    else:
        warn(rep, "i18n-key-parity", cat,
             "key set differs from en.json in: "
             + ", ".join(f"{c}({n})" for c, n in sorted(gap_langs.items()))[:200])


def check_docker(rep: ProductReport, p: Path):
    cat = "Docker"
    fe_df, be_df = p / "frontend/Dockerfile", p / "backend/Dockerfile"
    have_fe, have_be = fe_df.is_file(), be_df.is_file()
    if have_fe and have_be:
        ok(rep, "dockerfiles", cat, "frontend/Dockerfile and backend/Dockerfile present")
    elif have_fe or have_be:
        bad(rep, "dockerfiles", cat,
            "only one of frontend/backend has a Dockerfile — buyers cannot run the full stack")
    else:
        bad(rep, "dockerfiles", cat, "no Dockerfiles")

    comp = first(p, "docker-compose.yml", "docker-compose.yaml", "compose.yml")
    if comp:
        c = read(comp)
        services = re.findall(r"^\s{2}([a-z0-9_-]+):\s*$", c, re.M)
        health = "healthcheck" in c
        if len(services) >= 3:
            ok(rep, "compose-services", cat,
               f"{len(services)} services: {', '.join(services[:8])}"
               + (" (healthchecks present)" if health else " — no healthchecks"))
        else:
            bad(rep, "compose-services", cat,
                f"compose defines only {len(services)} service(s); a sellable stack needs app+db+cache",
                comp.name)
    else:
        bad(rep, "compose", cat, "no docker-compose.yml")

    df_text = read(fe_df) if have_fe else ""
    if have_fe:
        multi = "AS " in df_text.upper()
        pinned = re.search(r"FROM\s+node:[0-9.]+-alpine", df_text)
        if multi:
            ok(rep, "docker-multistage", cat, "frontend Dockerfile is multi-stage")
        else:
            warn(rep, "docker-multistage", cat, "frontend Dockerfile is single-stage")
        if pinned:
            ok(rep, "docker-pinned-base", cat, "pinned alpine base image")
        else:
            warn(rep, "docker-pinned-base", cat, "frontend Dockerfile base image not pinned")


def check_cicd(rep: ProductReport, p: Path):
    cat = "CI/CD"
    wfd = p / ".github/workflows"
    wfs = {q.name: read(q) for q in wfd.glob("*.y*ml")} if wfd.is_dir() else {}
    if not wfs:
        bad(rep, "workflows-present", cat, "no .github/workflows")
        return
    ok(rep, "workflows-present", cat, f"workflows: {', '.join(sorted(wfs))}")

    ci = next((v for k, v in wfs.items() if k == "ci.yml"), "")
    if not ci:
        warn(rep, "ci-workflow", cat, "no ci.yml")
    else:
        # A root-level `npm ci` is fatal when the repo root has no package.json.
        root_pkg = (p / "package.json").is_file()
        bad_working = "working-directory: frontend" not in ci and "working-directory: ./frontend" not in ci
        uses_ci = "npm ci" in ci
        if uses_ci and bad_working and not root_pkg:
            bad(rep, "ci-runs-install", cat,
                "CI runs `npm ci` but the repo root has no package.json — the pipeline fails on its first step",
                "ci.yml")
        elif uses_ci:
            ok(rep, "ci-runs-install", cat, "CI installs dependencies with npm ci")

        # `|| true` inside a cleanup trap is legitimate shell hygiene, not
        # failure masking. Only count it where it would hide a real step result.
        masked_lines = [
            ln for ln in ci.splitlines()
            if re.search(r"\|\|\s*true", ln)
            and not re.search(r"\btrap\b|\bkill\b|\brm\b|\brmdir\b", ln)
        ]
        masked = len(masked_lines)
        if masked:
            bad(rep, "ci-no-error-masking", cat,
                f"CI masks failures with `|| true` in {masked} step(s) — a green build proves nothing",
                "ci.yml")
        else:
            ok(rep, "ci-no-error-masking", cat, "no `|| true` failure masking in CI")

        if re.search(r"npm run build", ci):
            ok(rep, "ci-build", cat, "CI runs the frontend build")
        else:
            warn(rep, "ci-build", cat, "CI never builds the frontend")

        if "/health" in ci:
            ok(rep, "ci-boot-probe", cat, "CI boots the API and probes /health")
        elif re.search(r"npm (?:run )?test", ci):
            ok(rep, "ci-test", cat, "CI runs the backend test suite")
        else:
            warn(rep, "ci-boot-probe", cat,
                 "CI neither boots the API nor runs its tests — nothing verifies the backend")

    deploy = [k for k in wfs if "deploy" in k.lower() or "pages" in k.lower()]
    if deploy:
        body = "\n".join(wfs[k] for k in deploy)
        if "actions/deploy-pages" in body or "peaceiris/actions-gh-pages" in body:
            ok(rep, "deploy-pages", cat, f"GitHub Pages deploy workflow: {', '.join(deploy)}")
        else:
            warn(rep, "deploy-pages", cat, f"deploy workflow present ({', '.join(deploy)}) but no Pages action")
    else:
        bad(rep, "deploy-pages", cat, "no deployment workflow — nothing can go live automatically")


def check_live(rep: ProductReport, p: Path):
    cat = "Live demo"
    cfg = first(p, "frontend/vite.config.js", "frontend/vite.config.ts")
    if cfg:
        c = read(cfg)
        # `base` may be a quoted literal ('./'), an expression
        # (process.env.VITE_BASE_PATH || '/'), or absent entirely.
        m = re.search(r"base\s*:\s*(.+)", c)
        base = m.group(1).strip().rstrip(",") if m else "(unset)"
        if base in ("./", ""):
            ok(rep, "vite-base", cat, f"vite base = {base!r} (relative — works under a Pages subpath)")
        elif "VITE_BASE_PATH" in base or "import.meta.env" in base:
            ok(rep, "vite-base", cat,
               "vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath "
               "and for a custom domain alike")
        else:
            warn(rep, "vite-base", cat, f"vite base = {base!r} — verify it matches the live URL path")

        if "process.env" in c or "import.meta.env" in c:
            ok(rep, "vite-env-config", cat, "vite config reads environment variables")
    else:
        bad(rep, "vite-config", cat, "no vite.config — cannot build or deploy")

    # Deep links must not 404 on a static host. Either HashRouter, or a
    # BrowserRouter whose 404 fallback is regenerated from the real build.
    r = read(p / "frontend/src/App.jsx")
    postbuild = p / "frontend/scripts/postbuild-spa-fallback.mjs"
    build = ""
    pj = p / "frontend/package.json"
    if pj.is_file():
        build = str(load_json(pj).get("scripts", {}).get("build", ""))
    if "HashRouter" in r:
        ok(rep, "spa-routing", cat, "HashRouter — deep links survive static hosting")
    elif "BrowserRouter" in r:
        if postbuild.is_file() and "postbuild-spa-fallback" in build:
            ok(rep, "spa-routing", cat,
               "BrowserRouter with a 404.html fallback regenerated on every build")
        elif (p / "frontend/public/404.html").is_file():
            warn(rep, "spa-routing", cat,
                 "a static 404.html ships, but it is not regenerated at build time "
                 "— it will reference stale asset hashes after the next build")
        else:
            bad(rep, "spa-routing", cat,
                "BrowserRouter with no 404.html fallback — every deep link 404s on static hosting")
    else:
        warn(rep, "spa-routing", cat, "no router detected in App.jsx")

    live = first(p, "LIVE_URL.txt")
    live_url = read(live).strip() if live else ""
    if live_url and re.search(r"https?://\S+", live_url):
        ok(rep, "live-url-recorded", cat, f"live URL recorded: {live_url[:80]}")

        # GitHub Pages paths are case-sensitive. A canonical written with the
        # brand's display casing (`/ClaimFlow`) 404s while the deployment sits
        # live at the repo casing (`/claimflow`), and since LIVE_URL.txt is the
        # source every canonical, sitemap, Open Graph and hreflang entry copies
        # from, one wrong letter de-indexes the product. Verify the recorded
        # URL is actually the one the rest of the package points at.
        m = re.search(r"https?://[^/\s]+/(\S+)", live_url)
        if m and m.group(1).rstrip("/") != m.group(1).rstrip("/").lower():
            bad(rep, "live-url-casing", cat,
                f"LIVE_URL.txt uses mixed-case path '/{m.group(1)}' — GitHub Pages is "
                f"case-sensitive, so this 404s", f"expected '/{m.group(1).lower()}'")
        else:
            host = re.search(r"https?://([^/\s]+)", live_url).group(1)
            stray = []
            for f in walk_files(p):
                if f.suffix.lower() not in {".html", ".xml", ".json", ".md", ".txt", ".js", ".jsx"}:
                    continue
                if "node_modules" in f.parts or f == live:
                    continue
                body = read(f)
                for other in re.findall(r"https?://[^/\s]+/[A-Za-z0-9._-]+", body):
                    if other.startswith(live_url):
                        continue
                    # a different Pages path under the same owner
                    if other.split("/")[2] == host:
                        stray.append(f"{f.relative_to(p).as_posix()}: {other}")
            stray = sorted(set(stray))
            if stray:
                bad(rep, "live-url-consistent", cat,
                    f"{len(stray)} reference(s) point at a different Pages path than LIVE_URL.txt",
                    stray[0])
            else:
                ok(rep, "live-url-consistent", cat,
                   f"every shipped reference matches {live_url[:60]}")
    else:
        warn(rep, "live-url-recorded", cat, "no LIVE_URL.txt")


def check_docs(rep: ProductReport, p: Path):
    cat = "Documentation"
    md = {q.name.upper(): q for q in p.glob("*.md")}
    required = [
        ("README.md", "readme"),
        ("DEPLOYMENT.md", "deployment-guide"),
        ("LICENSE.md", "license"),
        ("SECURITY.md", "security-policy"),
        ("CHANGELOG.md", "changelog"),
        ("BUYER_DOCUMENTATION.md", "buyer-docs"),
        ("LEMON_SQUEEZY_SELLER_KIT.md", "seller-kit"),
        ("COMMERCIAL_LICENSE.md", "commercial-license"),
        ("CONTRIBUTING.md", "contributing"),
    ]
    for fname, check in required:
        doc = md.get(fname.upper())
        if doc is not None:
            size = doc.stat().st_size
            if size < 400:
                warn(rep, f"doc-{check}", cat, f"{doc.name} is only {size} bytes — too thin to sell")
            else:
                ok(rep, f"doc-{check}", cat, f"{doc.name} ({size:,} bytes)")
        else:
            bad(rep, f"doc-{check}", cat, f"missing {fname}")

    # README must not read like generated filler.
    rm = md.get("README.MD")
    if rm:
        t = read(rm)
        hits = [lab for rx, lab, cs in PLACEHOLDER_PATTERNS
                if re.search(rx, t, 0 if cs else re.I)]
        if hits:
            bad(rep, "readme-no-placeholders", cat,
                f"README contains placeholder text: {', '.join(hits)}", "README.md")
        else:
            ok(rep, "readme-no-placeholders", cat, "README is free of placeholder text")
        if len(t) < 800:
            warn(rep, "readme-substance", cat, f"README is {len(t)} chars — thin for a commercial product")
        else:
            ok(rep, "readme-substance", cat, f"README is {len(t):,} chars")

    # Support contact must be real enough to answer a refund request.
    contact = grep(p, r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)
    docs_contact = [c for c in contact if c[0].suffix.lower() == ".md"]
    if docs_contact:
        ok(rep, "support-contact", cat, f"{len(docs_contact)} support email reference(s) in docs")
    else:
        bad(rep, "support-contact", cat, "no support email anywhere in the documentation")


def check_licensing(rep: ProductReport, p: Path):
    cat = "Licensing"
    lic = first(p, "LICENSE.md", "LICENSE.txt", "LICENSE")
    if not lic:
        bad(rep, "license-present", cat, "no LICENSE file")
        return
    t = read(lic)
    if re.search(r"MIT|Apache|GNU|BSD", t, re.I):
        ok(rep, "license-present", cat, f"{lic.name} references a recognised licence")
    else:
        warn(rep, "license-present", cat, f"{lic.name} does not name a recognised licence")

    seal = first(p, "LICENSE-SEAL.md", "LICENSE_NOTICE.txt")
    if seal:
        ok(rep, "license-seal", cat, f"{seal.name} present")
    else:
        warn(rep, "license-seal", cat, "no LICENSE-SEAL / LICENSE_NOTICE for buyer provenance")

    ts = first(p, "THIRD_PARTY_NOTICES.md")
    if ts:
        ok(rep, "third-party-notices", cat, "THIRD_PARTY_NOTICES.md present")
    else:
        warn(rep, "third-party-notices", cat, "no third-party attribution file")


def check_provenance(rep: ProductReport, p: Path):
    """A product you sell must not carry traces of how it was produced."""
    cat = "Provenance"

    # Absolute developer paths leak the author's account name, their personal
    # folder layout, and the internal structure of the tool that made this.
    leaks = grep(p, r"[A-Za-z]:[/\\]+Users[/\\]|OneDrive[/\\]Desktop|generated-projects[/\\]")
    if leaks:
        f, ln, txt = leaks[0]
        bad(rep, "no-developer-paths", cat,
            f"{len(leaks)} absolute developer path(s) in shipped files",
            f"{f.relative_to(p).as_posix()}:{ln}  {txt[:90]}")
    else:
        ok(rep, "no-developer-paths", cat, "no absolute developer paths")

    attrib = grep(p, r"generated by Lumi[Cc]ore|built with Lumi[Cc]ore|"
                       r"Lumi[Cc]orePro|AI-generated by|ai-generated by")
    if attrib:
        f, ln, txt = attrib[0]
        bad(rep, "no-generator-attribution", cat,
            f"{len(attrib)} generator attribution string(s)",
            f"{f.relative_to(p).as_posix()}:{ln}  {txt[:90]}")
    else:
        ok(rep, "no-generator-attribution", cat, "no generator attribution")

    # A .git directory or a prebuilt archive inside a deliverable ships the
    # repository history — which can carry credentials — along with stale code.
    stray = []
    for child in p.iterdir():
        if child.is_dir() and child.name == ".git":
            stray.append(".git/")
        elif child.is_file() and child.suffix in {".zip", ".tar", ".gz", ".7z"}:
            stray.append(child.name)
    if stray:
        bad(rep, "no-stray-vcs-or-archives", cat,
            f"deliverable contains {len(stray)} stray artefact(s): {', '.join(stray[:5])}")
    else:
        ok(rep, "no-stray-vcs-or-archives", cat, "no .git directory or bundled archives")


DENIED_SECRETS_ARRAY = re.compile(r"DENIED_SECRETS\s*=\s*\[(.*?)\]", re.S)


def in_secret_denylist(f: Path, ln: int, txt: str) -> bool:
    """True when the hit sits inside a DENIED_SECRETS array.

    Those arrays list the weak secrets a loader refuses to boot with. Listing
    "changeme" there is the guard working, not unfinished content.
    """
    try:
        content = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    m = DENIED_SECRETS_ARRAY.search(content)
    if not m:
        return False
    first = content[: m.start(1)].count("\n") + 1
    last = first + m.group(1).count("\n")
    return first <= ln <= last


def check_placeholders(rep: ProductReport, p: Path):
    cat = "Content hygiene"
    # Seed/demo scripts legitimately contain example.com addresses, and input
    # fields legitimately show "you@example.com" as a hint. Only runtime code
    # and documentation count.
    excluded = ("seed", "scripts/seed", "production-seed")
    hits = []
    for rx, label, cs in PLACEHOLDER_PATTERNS:
        for f, ln, txt in grep(p, rx, 0 if cs else re.I):
            rel = f.relative_to(p).as_posix()
            if any(x in f.name.lower() for x in excluded):
                continue
            if f.suffix.lower() == ".md" and "CHANGELOG" in f.name.upper():
                continue
            # An email-shaped example.com inside a JSX placeholder attribute is
            # a helpful hint, not unfinished content.
            if label == "example.com placeholder domain" and 'placeholder=' in txt:
                continue
            # A weak-secret entry inside a DENIED_SECRETS array is a guard that
            # refuses to boot with that value, not unfinished content.
            if in_secret_denylist(f, ln, txt):
                continue
            hits.append((f, ln, label, txt))
    if hits:
        by_label: dict[str, list] = {}
        for f, ln, label, txt in hits:
            by_label.setdefault(label, []).append((f, ln, txt))
        label, ex = max(by_label.items(), key=lambda kv: len(kv[1]))
        f, ln, txt = ex[0]
        bad(rep, "no-placeholder-text", cat,
            f"{len(hits)} placeholder occurrence(s); most common: {label} x{len(ex)}",
            f"{f.relative_to(p).as_posix()}:{ln}  {txt}")
    else:
        ok(rep, "no-placeholder-text", cat, "no placeholder or filler text in shipped code or docs")


def check_backend(rep: ProductReport, p: Path):
    cat, be = "Backend", p / "backend"
    if not be.is_dir():
        bad(rep, "backend-present", cat, "no backend/ directory")
        return

    routes = be / "routes"
    names = sorted(q.name.lower() for q in routes.glob("*.js")) if routes.is_dir() else []
    if not names:
        bad(rep, "backend-routes", cat, "no backend/routes/*.js")
    else:
        ok(rep, "backend-routes", cat, f"{len(names)} route modules")

    auth = [n for n in names if n.startswith("auth")]
    if auth:
        body = read(routes / auth[0])
        has_reg = bool(re.search(r"/register|router\.post\(\s*['\"]/?signup", body))
        has_log = bool(re.search(r"/login|router\.post\(\s*['\"]/?signin", body))
        if has_reg and has_log:
            ok(rep, "backend-auth-endpoints", cat,
               f"{auth[0]} exposes both register and login")
        else:
            bad(rep, "backend-auth-endpoints", cat,
                f"{auth[0]} missing {'signup' if not has_reg else 'login'} endpoint")
    else:
        bad(rep, "backend-auth-endpoints", cat, "no auth route module")

    jwt = re.search(r"jsonwebtoken|jwt\.", read(be / "package.json")) if (be / "package.json").is_file() else None
    if jwt:
        ok(rep, "backend-jwt", cat, "JWT dependency declared")
    else:
        warn(rep, "backend-jwt", cat, "no JWT dependency — sessions cannot be signed")

    health = [n for n in names if "health" in n]
    srv = read(first(be, "server.js") or (be / "server.js"))
    if health or "/health" in srv:
        ok(rep, "backend-health", cat, "health endpoint present")
    else:
        warn(rep, "backend-health", cat, "no health endpoint — Docker/orchestrators cannot probe it")

    env_ex = (be / ".env.example").is_file()
    if env_ex:
        ok(rep, "backend-env-example", cat, "backend/.env.example present")
    else:
        bad(rep, "backend-env-example", cat, "no backend/.env.example")

    if (p / "database").is_dir():
        sql = list((p / "database").rglob("*.sql"))
        ok(rep, "database-schema", cat, f"database schema files: {len(sql)}")
    else:
        warn(rep, "database-schema", cat, "no database/ directory")


def check_syntax(rep: ProductReport, p: Path):
    """Parse every shipped backend JS file with Node's real ESM parser.

    Python cannot parse JavaScript, and `node --check` rejects top-level
    `import` inside .js files, so we delegate to a small Node helper that uses
    vm.SourceTextModule to parse without executing.
    """
    cat, be = "Code health", p / "backend"
    if not be.is_dir():
        return
    targets = [str(f) for f in walk_files(be, {".js", ".mjs"})]
    if not targets:
        warn(rep, "backend-syntax", cat, "no backend JavaScript to parse")
        return

    helper = ROOT / "scripts/js_parse_check.mjs"
    try:
        proc = subprocess.run(
            ["node", "--experimental-vm-modules", str(helper), *targets],
            capture_output=True, text=True, timeout=180, cwd=str(ROOT),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        warn(rep, "backend-syntax", cat, f"could not run the Node parser: {exc}")
        return

    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        warn(rep, "backend-syntax", cat,
             f"Node parser returned non-JSON output: {(proc.stderr or '')[:160]}")
        return

    failures = data.get("failures", [])
    if failures:
        f0 = failures[0]
        rel = Path(f0["file"]).relative_to(p).as_posix()
        bad(rep, "backend-syntax", cat,
            f"{len(failures)} of {data.get('checked', 0)} backend file(s) fail to parse: {f0['message']}",
            f"{rel}:{f0['line']}")
    else:
        ok(rep, "backend-syntax", cat,
           f"all {data.get('checked', 0)} backend JavaScript files parse")


def check_imports_resolve(rep: ProductReport, p: Path):
    """Every relative import in the shipped frontend must point at a real file.

    Vite only compiles what `src/main.jsx` reaches, so a stray file that the
    entry never touches still ships, still looks like product code to a buyer,
    and still fails the moment anyone opens it. A package that advertises
    `../../_shared/TemplateShell` when no `_shared` directory exists is the
    kind of thing that costs a sale, so resolve the whole tree rather than just
    the reachable graph.
    """
    cat = "Code health"
    fe = p / "frontend"
    if not fe.is_dir():
        return

    exts = ("", ".jsx", ".js", ".mjs", ".json", ".css", "/index.jsx", "/index.js")
    checked = unresolved = 0
    first = None

    for f in walk_files(fe, {".js", ".jsx", ".mjs"}):
        if "node_modules" in f.parts:
            continue
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        checked += 1
        for m in re.finditer(r"""(?:from|import)\s+['"](\.[^'"]+)['"]""", src):
            target = (f.parent / m.group(1)).resolve()
            if not any(Path(str(target) + e).exists() for e in exts):
                unresolved += 1
                if first is None:
                    first = f"{f.relative_to(p).as_posix()}: {m.group(1)}"

    if not checked:
        return
    if unresolved:
        bad(rep, "frontend-imports-resolve", cat,
            f"{unresolved} relative import(s) in {checked} frontend file(s) point at a "
            f"file that does not exist", first)
    else:
        ok(rep, "frontend-imports-resolve", cat,
           f"every relative import in {checked} frontend files resolves")


def check_service_worker(rep: ProductReport, p: Path):
    """A Pages subpath app must not use root-absolute URLs in its service worker.

    These demos publish to `https://<owner>.github.io/<repo>/`, so a URL written
    as `/sw.js` or `/offline.html` resolves to the apex domain where nothing
    answers, and a worker registered at scope `/` claims every repository on that
    Pages host rather than this one. Both fail silently: the app still loads, so
    only an offline visit or a cache inspection reveals it.
    """
    cat = "Code health"
    sw = p / "frontend/public/sw.js"
    reg = p / "frontend/src/sw-register.js"
    if not sw.is_file() and not reg.is_file():
        return

    problems = []
    for path in (sw, reg):
        if not path.is_file():
            continue
        body = read(path)
        for m in re.finditer(r"""['"](/(?:sw\.js|offline\.html|index\.html))['"]""", body):
            problems.append(f"{path.relative_to(p).as_posix()}: {m.group(1)} is root-absolute")
        # a scope of '/' would control the whole Pages host, not this repo
        for m in re.finditer(r"scope['\"]?\s*[:=]\s*['\"]/['\"]", body):
            problems.append(f"{path.relative_to(p).as_posix()}: scope '/' is the Pages apex")

    if problems:
        bad(rep, "service-worker-subpath", cat,
            f"{len(problems)} root-absolute path(s) - the app is served from a "
            f"Pages subpath, so these resolve to the apex domain", problems[0])
    else:
        ok(rep, "service-worker-subpath", cat,
           "service worker URLs and scope are base-relative")


GROUPS: list[tuple[str, Callable[[ProductReport, Path], None]]] = [
    ("security", check_security),
    ("provenance", check_provenance),
    ("dependencies", check_dependencies),
    ("frontend", check_frontend),
    ("i18n", check_i18n),
    ("docker", check_docker),
    ("cicd", check_cicd),
    ("live", check_live),
    ("docs", check_docs),
    ("licensing", check_licensing),
    ("placeholders", check_placeholders),
    ("backend", check_backend),
    ("syntax", check_syntax),
    ("imports", check_imports_resolve),
    ("service-worker", check_service_worker),
]


def audit_product(name: str, path: Path) -> ProductReport:
    rep = ProductReport(name=name, path=path.relative_to(ROOT).as_posix())
    for _, fn in GROUPS:
        try:
            fn(rep, path)
        except Exception as exc:  # a crashing check is itself a finding
            rep.add("audit-error", "audit", FAIL, f"check raised {type(exc).__name__}: {exc}")
    return rep


def discover(only: Optional[str] = None) -> list[Path]:
    if not PRODUCTS_DIR.is_dir():
        return []
    dirs = sorted(q for q in PRODUCTS_DIR.iterdir() if q.is_dir() and not q.name.startswith("."))
    if only:
        dirs = [q for q in dirs if only in q.name]
    return dirs


C = {"PASS": "\033[32m", "FAIL": "\033[31m", "WARN": "\033[33m"}
R = "\033[0m"


def render(reports: list[ProductReport], colour: bool) -> str:
    out: list[str] = []
    total_fail = sum(len(r.fails) for r in reports)
    for r in reports:
        npass = len(r.findings) - len(r.fails) - len(r.warns)
        verdict = "SELLABLE" if r.sellable else "NOT SELLABLE"
        banner = (f"{r.name.upper()}  —  score {r.score}/100   "
                  f"{npass} pass, {len(r.warns)} warn, {len(r.fails)} fail   [{verdict}]")
        out += ["", "=" * 78, banner, "=" * 78]
        for f in r.findings:
            tag = f.status
            if colour:
                tag = f"{C[f.status]}{f.status}{R}"
            line = f"  [{tag}] {f.category:<22} {f.check:<28} {f.detail}"
            out.append(line)
            if f.evidence:
                out.append(f"            └─ {f.evidence}")
    out.append("\n" + "=" * 78)
    out.append(f"TOTAL: {len(reports)} products, {total_fail} failing checks")
    out.append("=" * 78)
    return "\n".join(out)


def write_reports(reports: list[ProductReport]) -> None:
    payload = {
        "generatedAt": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "products": [
            {
                "name": r.name,
                "path": r.path,
                "score": r.score,
                "sellable": r.sellable,
                "counts": {
                    "pass": len(r.findings) - len(r.fails) - len(r.warns),
                    "warn": len(r.warns),
                    "fail": len(r.fails),
                },
                "findings": [asdict(f) for f in r.findings],
            }
            for r in reports
        ],
    }
    (PRODUCTS_DIR / "AUDIT.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md = ["# Product Sellability Audit", "",
          f"_Generated {payload['generatedAt']}_", "",
          "| Product | Score | Pass | Warn | Fail | Verdict |",
          "|---|---:|---:|---:|---:|---|"]
    for r in reports:
        md.append(f"| [{r.name}]({r.name}/) | {r.score}/100 | "
                  f"{len(r.findings)-len(r.fails)-len(r.warns)} | {len(r.warns)} | "
                  f"{len(r.fails)} | {'✅ sellable' if r.sellable else '❌ not sellable'} |")
    for r in reports:
        md += ["", f"## {r.name} — {r.score}/100", "",
               "| Status | Category | Check | Detail |", "|---|---|---|---|"]
        for f in r.findings:
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[f.status]
            ev = f" — `{f.evidence}`" if f.evidence else ""
            md.append(f"| {icon} {f.status} | {f.category} | `{f.check}` | {f.detail}{ev} |")
    (PRODUCTS_DIR / "AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="filter to a single product name")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    ap.add_argument("--write-reports", action="store_true",
                    help="write products/AUDIT.json and products/AUDIT.md")
    ap.add_argument("--no-colour", action="store_true")
    a = ap.parse_args()

    dirs = discover(a.only)
    if not dirs:
        print(f"No products found in {PRODUCTS_DIR}", file=sys.stderr)
        return 2

    reports = [audit_product(d.name, d) for d in dirs]
    if a.write_reports:
        write_reports(reports)
        print(f"Wrote {PRODUCTS_DIR/'AUDIT.json'} and {PRODUCTS_DIR/'AUDIT.md'}")

    if a.json:
        print(json.dumps({
            "products": [{
                "name": r.name, "score": r.score, "sellable": r.sellable,
                "findings": [asdict(f) for f in r.findings],
            } for r in reports]
        }, indent=2))
    else:
        print(render(reports, colour=not a.no_colour and sys.stdout.isatty()))

    return 1 if any(r.fails for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())