"""Repository reverse-engineering analyser (clean-room, read-only).

Purpose
-------
When an operator is asked to rebuild, modernise or price work on an EXISTING
codebase, the factory needs a factual picture of that codebase before planning.
This module produces it without executing, importing or copying anything:

    scan_repository(path)            -> stack / routes / models / tests / risks
    build_reconstruction_plan(scan)  -> clean-room rebuild blueprint
    reverse_engineer(path)           -> both, plus a rendered markdown report

Hard rules (enforced in code):
- READ-ONLY. No imports of the target code, no shell, no network, no writes.
- Skips VCS/vendor/build directories (node_modules, .git, dist, venv, ...).
- Ignores files larger than ``MAX_FILE_BYTES`` and stops after ``MAX_FILES``.
- Produces a PLAN, never extracted source: callers must only use this on
  repositories they own or are licensed to analyse.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

MAX_FILES = 5000
MAX_FILE_BYTES = 1_000_000
SKIP_DIRS = {
    "node_modules", ".git", ".hg", ".svn", "venv", ".venv", "__pycache__",
    "dist", "build", ".next", ".nuxt", ".cache", "coverage", "logs",
    "test-results", "playwright-report", ".idea", ".vscode", "pgdata",
    ".pytest_cache", ".mypy_cache", "vendor", "target",
}
TEXT_EXTS = {
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".go", ".rb", ".php",
    ".java", ".cs", ".vue", ".svelte", ".html", ".css", ".scss", ".sql",
    ".json", ".yml", ".yaml", ".toml", ".md", ".env", ".example", ".prisma",
    ".sh", ".dockerfile",
}

ROUTE_PATTERNS = [
    re.compile(r"router\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]", re.I),
    re.compile(r"app\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]", re.I),
    re.compile(r"@\w+\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"@app\.route\(\s*['\"]([^'\"]+)['\"].*?methods\s*=\s*\[([^\]]+)\]", re.I | re.S),
]
MODEL_PATTERNS = [
    re.compile(r"sequelize\.define\(\s*['\"]([A-Za-z0-9_]+)['\"]"),
    re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", re.I),
    re.compile(r"^\s*model\s+([A-Za-z0-9_]+)\s*\{", re.M),
    re.compile(r"class\s+([A-Za-z0-9_]+)\s*\(\s*models\.Model\s*\)"),
]
ENV_PATTERNS = [
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"os\.environ\[\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
]
SECRET_HINTS = [
    re.compile(r"sk_live_[A-Za-z0-9]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][A-Za-z0-9+/=_-]{16,}['\"]"),
]

FRAMEWORK_HINTS = {
    "react": "React", "react-dom": "React", "vue": "Vue", "svelte": "Svelte",
    "@angular/core": "Angular", "next": "Next.js", "nuxt": "Nuxt",
    "express": "Express", "fastify": "Fastify", "koa": "Koa", "hapi": "Hapi",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "sequelize": "Sequelize", "prisma": "Prisma", "mongoose": "Mongoose",
    "typeorm": "TypeORM", "knex": "Knex", "@tanstack/react-query": "React Query",
    "tailwindcss": "Tailwind CSS", "vite": "Vite", "webpack": "Webpack",
    "jest": "Jest", "vitest": "Vitest", "pytest": "pytest", "playwright": "Playwright",
    "@playwright/test": "Playwright", "stripe": "Stripe", "nodemailer": "Nodemailer",
}

INTEGRATION_GROUPS = {
    "payments": ("STRIPE", "PAYPAL", "RAZORPAY", "SQUARE", "MOLLIE", "PADDLE",
                 "FLUTTERWAVE", "PAYTM", "LIQPAY", "MERCADOPAGO", "BKASH"),
    "ai": ("OPENAI", "ANTHROPIC", "GEMINI", "DEEPSEEK", "MISTRAL", "GROK",
           "OPENROUTER", "NVIDIA", "AI_"),
    "database": ("DATABASE", "DB_", "POSTGRES", "MYSQL", "MONGO", "REDIS"),
    "auth": ("JWT", "AUTH", "OAUTH", "SESSION", "CLERK", "AUTH0"),
    "email": ("SMTP", "MAIL", "EMAIL", "SENDGRID", "RESEND"),
    "storage": ("S3", "R2", "CLOUDINARY", "UPLOAD", "STORAGE"),
}


def _iter_source_files(root: Path, max_files: int = MAX_FILES) -> Iterable[Path]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d.lower() not in SKIP_DIRS)
        for name in sorted(filenames):
            if count >= max_files:
                return
            p = Path(dirpath) / name
            try:
                if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            count += 1
            yield p


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _language_stats(files: List[Path]) -> Dict[str, int]:
    languages: Counter = Counter()
    for f in files:
        ext = f.suffix.lower()
        if ext in TEXT_EXTS:
            languages[ext or "unknown"] += 1
    return dict(languages.most_common())


def _detect_stack(root: Path, texts: Dict[Path, str]) -> Dict[str, Any]:
    frameworks: set = set()
    package_meta: Dict[str, Any] = {}
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(_read(pkg) or "{}")
            package_meta = {
                "name": data.get("name"),
                "scripts": list((data.get("scripts") or {}).keys()),
                "dependencies": list((data.get("dependencies") or {}).keys()),
                "devDependencies": list((data.get("devDependencies") or {}).keys()),
            }
            for dep in list(package_meta["dependencies"]) + list(package_meta["devDependencies"]):
                if dep in FRAMEWORK_HINTS:
                    frameworks.add(FRAMEWORK_HINTS[dep])
        except (json.JSONDecodeError, OSError):
            package_meta = {}

    for req_name in ("requirements.txt", "pyproject.toml", "Pipfile"):
        req = root / req_name
        if req.is_file():
            content = _read(req).lower()
            for key, label in (("fastapi", "FastAPI"), ("django", "Django"),
                               ("flask", "Flask"), ("pytest", "pytest")):
                if key in content:
                    frameworks.add(label)

    if (root / "go.mod").is_file():
        frameworks.add("Go module")
    if (root / "composer.json").is_file():
        frameworks.add("PHP/Composer")
    if (root / "Gemfile").is_file():
        frameworks.add("Ruby/Bundler")

    entry_points = []
    for candidate in ("server.js", "index.js", "src/main.jsx", "src/index.js",
                      "main.py", "app.py", "server.py", "manage.py"):
        if (root / candidate).is_file():
            entry_points.append(candidate)

    return {
        "frameworks": sorted(frameworks),
        "package": package_meta,
        "entry_points": entry_points,
    }


def _detect_routes(texts: Dict[Path, str]) -> List[Dict[str, str]]:
    routes: List[Dict[str, str]] = []
    for path, text in texts.items():
        if path.suffix.lower() not in {".js", ".jsx", ".ts", ".tsx", ".py"}:
            continue
        for pattern in ROUTE_PATTERNS:
            for m in pattern.finditer(text):
                groups = m.groups()
                if len(groups) >= 2:
                    method = (groups[0] or "GET").upper()
                    route = groups[1]
                    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                        method = "GET"
                        route = groups[0]
                    routes.append({
                        "method": method,
                        "path": route,
                        "file": str(path),
                    })
    # Next.js file-router endpoints
    for path in texts:
        parts = path.parts
        if "pages" in parts and "api" in parts and path.suffix.lower() in {".js", ".ts"}:
            routes.append({"method": "ANY", "path": "/" + str(path), "file": str(path)})
    # de-duplicate (method, path)
    seen = set()
    unique = []
    for r in routes:
        key = (r["method"], r["path"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique[:500]


def _detect_models(texts: Dict[Path, str]) -> List[str]:
    models: set = set()
    for text in texts.values():
        for pattern in MODEL_PATTERNS:
            for m in pattern.finditer(text):
                models.add(m.group(1).lower())
    return sorted(models)[:200]


def _detect_tests(files: List[Path]) -> Dict[str, Any]:
    test_files = [
        f for f in files
        if re.search(r"(\.test\.|\.spec\.|(^|/)tests?/)", str(f).replace("\\", "/"), re.I)
    ]
    return {"count": len(test_files), "files": [str(f) for f in test_files[:100]]}


def _detect_integrations(texts: Dict[Path, str]) -> Dict[str, List[str]]:
    envs: set = set()
    for text in texts.values():
        for pattern in ENV_PATTERNS:
            envs.update(pattern.findall(text))
    grouped: Dict[str, List[str]] = {}
    remaining = set(envs)
    for group, prefixes in INTEGRATION_GROUPS.items():
        matched = sorted(
            name for name in remaining if any(name.startswith(p) or p in name for p in prefixes)
        )
        if matched:
            grouped[group] = matched
            remaining.difference_update(matched)
    if remaining:
        grouped["other"] = sorted(remaining)[:60]
    grouped["all"] = sorted(envs)
    return grouped


def _detect_risks(root: Path, files: List[Path], texts: Dict[Path, str]) -> List[Dict[str, str]]:
    risks: List[Dict[str, str]] = []
    counts = Counter()
    for path, text in texts.items():
        for name, pattern in (
            ("dangerouslySetInnerHTML", re.compile(r"dangerouslySetInnerHTML")),
            ("eval", re.compile(r"\beval\s*\(")),
            ("child_process", re.compile(r"child_process")),
            ("sql-string-interpolation", re.compile(r"query\(\s*`[^`]*\$\{")),
        ):
            hits = len(pattern.findall(text))
            if hits:
                counts[name] += hits
                risks.append({"type": name, "file": str(path), "hits": str(hits)})
        for pattern in SECRET_HINTS:
            if pattern.search(text):
                counts["possible-secret"] += 1
                risks.append({"type": "possible-secret", "file": str(path), "hits": "1"})
                break

    if (root / ".env").is_file() or (root / ".env.local").is_file():
        # The analyser never shells out to git, so it cannot know whether the
        # file is tracked — claim presence on disk, nothing stronger.
        risks.append({"type": "env-file-on-disk", "file": ".env", "hits": "1"})
    if not (root / ".gitignore").is_file():
        risks.append({"type": "missing-gitignore", "file": ".gitignore", "hits": "1"})
    if not (root / ".env.example").is_file() and not (root / "backend" / ".env.example").is_file():
        risks.append({"type": "missing-env-example", "file": ".env.example", "hits": "1"})

    dedup: Dict[str, Dict[str, str]] = {}
    for r in risks:
        dedup.setdefault(r["type"], r)
    return list(dedup.values())


def _detect_quality_signals(root: Path) -> Dict[str, bool]:
    checks = {
        "eslint": ["eslint.config.js", ".eslintrc", ".eslintrc.js", ".eslintrc.json"],
        "prettier": [".prettierrc", ".prettierrc.json", "prettier.config.js"],
        "typescript": ["tsconfig.json"],
        "ci": [".github/workflows"],
        "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "tests_config": ["jest.config.js", "vitest.config.js", "vite.config.js", "pytest.ini", "pyproject.toml"],
        "readme": ["README.md"],
        "license": ["LICENSE", "LICENSE.md"],
    }
    return {
        key: any((root / c).exists() for c in candidates)
        for key, candidates in checks.items()
    }


def scan_repository(root: str | Path, *, max_files: int = MAX_FILES) -> Dict[str, Any]:
    """Read-only structural scan. Returns a JSON-serialisable dict."""
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise ValueError(f"Not a directory: {root_path}")

    files = list(_iter_source_files(root_path, max_files=max_files))
    texts: Dict[Path, str] = {}
    for f in files:
        try:
            rel = f.relative_to(root_path)
        except ValueError:
            continue
        if f.suffix.lower() in TEXT_EXTS or f.name in {"Dockerfile", "Makefile"}:
            texts[rel] = _read(f)

    total_bytes = sum(len(t) for t in texts.values())
    stack = _detect_stack(root_path, texts)

    return {
        "root": str(root_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "files_scanned": len(files),
            "text_bytes": total_bytes,
            "languages": _language_stats(files),
            "truncated": len(files) >= max_files,
        },
        "stack": stack,
        "routes": _detect_routes(texts),
        "data_models": _detect_models(texts),
        "tests": _detect_tests(files),
        "integrations": _detect_integrations(texts),
        "risks": _detect_risks(root_path, files, texts),
        "quality": _detect_quality_signals(root_path),
    }


def _guess_product_type(scan: Dict[str, Any]) -> str:
    frameworks = set(scan.get("stack", {}).get("frameworks", []))
    models = set(scan.get("data_models", []))
    routes = scan.get("routes", [])
    route_text = " ".join(r.get("path", "") for r in routes).lower()
    if {"Stripe", "PayPal", "Razorpay", "Square", "Paddle"} & frameworks or any(
        k in models for k in ("orders", "products", "cart_items")
    ) or any(k in route_text for k in ("checkout", "cart", "payment")):
        return "ecommerce"
    if any(k in models for k in ("subscriptions", "plans", "invoices")):
        return "saas"
    if "chat" in route_text or "ai" in route_text:
        return "ai_tool"
    if {"React", "Vue", "Svelte", "Next.js"} & frameworks and not models:
        return "marketing_site"
    return "web_app"


def build_reconstruction_plan(scan: Dict[str, Any]) -> Dict[str, Any]:
    """Turn the scan into a clean-room rebuild blueprint (no source copied)."""
    product_type = _guess_product_type(scan)
    routes = scan.get("routes", [])
    models = scan.get("data_models", [])
    tests = scan.get("tests", {})
    risks = scan.get("risks", [])
    stats = scan.get("stats", {})

    if stats.get("files_scanned", 0) > 1500 or len(routes) > 150:
        effort = "L"
    elif stats.get("files_scanned", 0) > 300 or len(routes) > 40:
        effort = "M"
    else:
        effort = "S"

    return {
        "product_type": product_type,
        "effort_estimate": effort,
        "pages_inventory": [r["path"] for r in routes if r["method"] == "GET"][:60],
        "api_surface": [
            {"method": r["method"], "path": r["path"]} for r in routes
        ][:200],
        "data_model": models,
        "feature_candidates": sorted({
            r["path"].strip("/").split("/")[0]
            for r in routes
            if r["path"].strip("/")
        })[:30],
        "test_baseline": {
            "existing_test_files": tests.get("count", 0),
            "recommendation": "port behaviour tests, not implementation code",
        },
        "risk_backlog": [f"{r['type']} ({r['file']})" for r in risks],
        "integration_plan": {
            k: v for k, v in scan.get("integrations", {}).items() if k != "all"
        },
        "modernisation": {
            "detected_frameworks": scan.get("stack", {}).get("frameworks", []),
            "note": "Replace/upgrade only where the scan shows risk or missing maintenance; keep proven behaviour.",
        },
        "legal_note": (
            "Clean-room analysis: this plan is generated from structure only. "
            "Only analyse repositories you own or are licensed to work on; do not "
            "copy source code or assets without permission."
        ),
    }


def render_report_markdown(result: Dict[str, Any]) -> str:
    scan = result.get("scan", {})
    plan = result.get("plan", {})
    stats = scan.get("stats", {})
    stack = scan.get("stack", {})
    lines = [
        "# Repository Reverse-Engineering Report",
        "",
        f"**Root:** `{scan.get('root', '')}`  ",
        f"**Generated:** {scan.get('generated_at', '')}  ",
        f"**Product type:** {plan.get('product_type', 'unknown')}  ",
        f"**Effort estimate:** {plan.get('effort_estimate', '?')}",
        "",
        "## Scan",
        f"- Files scanned: {stats.get('files_scanned', 0)}"
        f"{' (truncated)' if stats.get('truncated') else ''}",
        f"- Languages: {', '.join(f'{k} ({v})' for k, v in list(stats.get('languages', {}).items())[:8]) or '—'}",
        f"- Frameworks: {', '.join(stack.get('frameworks', [])) or '—'}",
        f"- Routes: {len(scan.get('routes', []))}",
        f"- Data models: {', '.join(scan.get('data_models', [])) or '—'}",
        f"- Existing test files: {scan.get('tests', {}).get('count', 0)}",
        "",
        "## Risks",
    ]
    risks = scan.get("risks", [])
    if risks:
        lines.extend(f"- {r['type']} — `{r['file']}`" for r in risks[:30])
    else:
        lines.append("- None detected")
    lines += ["", "## Reconstruction plan", "```json", json.dumps(plan, indent=2, ensure_ascii=False), "```", ""]
    return "\n".join(lines)


def reverse_engineer(root: str | Path, *, max_files: int = MAX_FILES) -> Dict[str, Any]:
    scan = scan_repository(root, max_files=max_files)
    plan = build_reconstruction_plan(scan)
    return {
        "scan": scan,
        "plan": plan,
        "report_markdown": render_report_markdown({"scan": scan, "plan": plan}),
    }


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Read-only repository analyser: structure, routes, models, risks, rebuild plan."
    )
    parser.add_argument("path", help="Repository directory to analyse")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of markdown")
    args = parser.parse_args(argv)

    result = reverse_engineer(args.path)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
