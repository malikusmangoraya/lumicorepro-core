"""Turn four frontend-only delivery snapshots into full-stack products.

The delivery snapshots ship only `src/` and a built `dist/`. Their React source
already uses the same conventions as the verified catalogue in `products/`
(React 19 + Vite, `@/` alias, Tailwind design tokens, i18next, Zustand,
React Query), so the build shell and the whole proven backend can be copied
across unchanged and only the brand strings need re-skinning.

    python scripts/port_fullstack.py
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core")
TEMPLATE = ROOT / "products" / "meridian-capital"
DELIVERY = ROOT / "delivery"

# slug -> (display name, live url)
TARGETS = {
    "kestrel-fleet": ("Kestrel Fleet", "https://malikusmangoraya.github.io/kestrel-fleet"),
    "maison-noir": ("Maison Noir", "https://malikusmangoraya.github.io/maison-noir"),
    "ledgerline": ("Ledgerline", "https://malikusmangoraya.github.io/ledgerline"),
    "kinetiq-health": ("Kinetiq Health", "https://malikusmangoraya.github.io/kinetiq-health"),
}

# Frontend build shell — everything except src/, which is the project's own.
FRONTEND_FILES = [
    "package.json", "package-lock.json", "vite.config.js",
    "vite.config.performance.js", "tailwind.config.js", "postcss.config.js",
    "index.html", "budget.json", "design-tokens.json", ".env.example",
    "Dockerfile", ".dockerignore", "nginx.conf",
]
FRONTEND_DIRS = ["public", "scripts"]

# Root-level infrastructure and documentation.
ROOT_FILES = [
    "docker-compose.yml", ".gitignore", ".env.production.example",
    ".lighthouserc.json", "cloudflare-rules.json", "railway.json",
    "render.yaml", "vercel.json", "netlify.toml", "cloudrun.yaml",
    "structured-data.json", "design-manifest.json",
    "favicon.svg", "logo.svg", "og-image.svg",
]
ROOT_DIRS = [".github", "aws", "nginx"]

DOC_NAMES = [
    "README.md", "DEPLOYMENT.md", "SECURITY.md", "CHANGELOG.md",
    "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md", "BUYER_DOCUMENTATION.md",
    "COMMERCIAL_LICENSE.md", "LEMON_SQUEEZY_SELLER_KIT.md",
    "BRAND_GUIDELINES.md", "LICENSE.md", "LICENSE-SEAL.md",
    "SUPPORT.md", "ROADMAP.md", "DEMO.md", "BACKUP.md", "ACCESSIBILITY.md",
    "COMPLIANCE.md", "PERFORMANCE.md", "SEO_META_TAGS.md", "SETUP_GUIDE.md",
    "WEBHOOKS.md", "SCHEMA-CONTRACT.md", "QA_REPORT.md", "ANALYTICS.md",
    "DEPLOYMENT_CHECKLIST.md", "SECURITY-CHECKLIST.md", "COPY_BRIEF.md",
    "README-MARKETING.md", "DESIGN-TOKENS.md", "DESIGN-PLAN.md",
    "DESIGN-STYLE.md", "MOTION_REPORT.md", "SEO_AUDIT.md", "A11Y_REPORT.md",
    "EXPERIMENTS.md", "CDN_DEPLOYMENT.md", "PLATFORM-INJECTION.md",
    "QUALITY-GATES.md", "DEPLOYMENT_GUIDE.md", "LICENSE_NOTICE.txt",
    "INSTRUCTIONS.md", "GENERATION-MATRIX.md",
]

SKIP_DIR_NAMES = {"node_modules", ".artifacts", ".do", "screenshots", "dist"}

TEXT_EXT = {".js", ".jsx", ".json", ".md", ".html", ".css", ".yml", ".yaml",
            ".svg", ".txt", ".cjs", ".mjs", ".example", ""}


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        if any(p in SKIP_DIR_NAMES for p in rel.parts):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        n += 1
    return n


def reskin(text: str, slug: str, brand: str) -> str:
    """Replace the template's identifiers with this project's own."""
    old_slug = "meridian-capital"
    old_brand = "Meridian"
    old_db = "meridian_capital"
    text = re.sub(rf"\b{re.escape(old_slug)}\b", slug, text)
    text = re.sub(rf"\b{re.escape(old_db)}\b", slug.replace("-", "_"), text)
    text = re.sub(rf"\b{re.escape(old_brand)} Capital\b", brand, text)
    text = re.sub(rf"\b{re.escape(old_brand)}\b", brand.split()[0], text)
    return text


def reskin_tree(root: Path, slug: str, brand: str) -> int:
    changed = 0
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if any(p in SKIP_DIR_NAMES for p in rel.parts):
            continue
        if f.suffix.lower() not in TEXT_EXT:
            continue
        try:
            t = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = reskin(t, slug, brand)
        if new != t:
            f.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def port(slug: str, brand: str, live: str) -> None:
    dst = DELIVERY / slug
    fe = dst / "frontend"

    # 1. keep the project's own frontend source
    fe.mkdir(parents=True, exist_ok=True)
    src_dir = dst / "src"
    if src_dir.is_dir():
        target = fe / "src"
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(src_dir), str(target))
    dist_dir = dst / "dist"
    if dist_dir.is_dir():
        target = fe / "dist"
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(dist_dir), str(target))

    # 2. build shell
    copied = 0
    for name in FRONTEND_FILES:
        s = TEMPLATE / "frontend" / name
        if s.is_file():
            shutil.copy2(s, fe / name)
            copied += 1
    for name in FRONTEND_DIRS:
        s = TEMPLATE / "frontend" / name
        if s.is_dir():
            copied += copy_tree(s, fe / name)

    # 3. proven backend
    copied += copy_tree(TEMPLATE / "backend", dst / "backend")

    # 4. root infra + docs
    for name in ROOT_FILES:
        s = TEMPLATE / name
        if s.is_file():
            shutil.copy2(s, dst / name)
            copied += 1
    for name in ROOT_DIRS:
        s = TEMPLATE / name
        if s.is_dir():
            copied += copy_tree(s, dst / name)
    for name in DOC_NAMES:
        s = TEMPLATE / name
        if s.is_file():
            shutil.copy2(s, dst / name)
            copied += 1

    # 5. brand
    changed = reskin_tree(fe, slug, brand)
    changed += reskin_tree(dst / "backend", slug, brand)

    # 6. identifiers that must be unique per project
    pkg_p = fe / "package.json"
    pkg = json.loads(pkg_p.read_text(encoding="utf-8"))
    pkg["name"] = f"{slug}-frontend"
    pkg_p.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    bpkg_p = dst / "backend" / "package.json"
    bpkg = json.loads(bpkg_p.read_text(encoding="utf-8"))
    bpkg["name"] = f"{slug}-backend"
    bpkg_p.write_text(json.dumps(bpkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    env_p = dst / "backend" / ".env.example"
    if env_p.is_file():
        t = env_p.read_text(encoding="utf-8")
        t = t.replace("APP_BRAND=", f"APP_BRAND={brand}")
        t = re.sub(r"DEMO_USER_EMAIL=.*", f"DEMO_USER_EMAIL=demo@{slug}.test", t)
        t = re.sub(r"DEMO_ADMIN_EMAIL=.*", f"DEMO_ADMIN_EMAIL=admin@{slug}.test", t)
        t = re.sub(r"LICENSE_PRODUCT=.*", f"LICENSE_PRODUCT={slug}", t)
        env_p.write_text(t, encoding="utf-8")

    live_p = dst / "LIVE-LINK.txt"
    live_p.write_text(f"LIVE LINK\n=========\n{live}\n", encoding="utf-8")

    print(f"{slug:<16} {copied:>4} files copied, {changed:>3} re-skinned")


def main() -> int:
    for slug, (brand, live) in TARGETS.items():
        if not (DELIVERY / slug / "src").is_dir() and not (DELIVERY / slug / "frontend" / "src").is_dir():
            print(f"skip {slug}: no frontend src found")
            continue
        port(slug, brand, live)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
