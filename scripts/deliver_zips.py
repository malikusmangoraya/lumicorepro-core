"""Create brand-named delivery copies + per-project ZIPs with LIVE-LINK.txt.

Each ZIP contains the full built site (dist) + source + README, and the ONLY
reference to the live link lives inside as LIVE-LINK.txt (plus kept off-site).
The folder in delivery/ carries the brand slug (aurelia-estates, not build-002).
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand_map import BRANDS

GEN = Path(__file__).resolve().parent.parent / "generated-projects"
OUT = Path(__file__).resolve().parent.parent / "delivery"
OUT.mkdir(parents=True, exist_ok=True)


def slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return base


URL_RE = re.compile(r"https?://[^\s'\"><)]+")


def homepage_of(proj: Path) -> str:
    """Resolve the site's real live URL.

    LIVE_URL.txt is authoritative: it records what the deploy actually
    published. `homepage` in package.json is a Create-React-App field that Vite
    projects do not set, so it can never be the primary source, and the
    conventional GitHub Pages URL is only a last-resort guess.
    """
    live = proj / "LIVE_URL.txt"
    if live.exists():
        for u in URL_RE.findall(live.read_text(errors="ignore")):
            if "github.io" in u:
                return u.rstrip("/")

    pj = proj / "frontend" / "package.json"
    if pj.exists():
        m = re.search(r'"homepage"\s*:\s*"([^"]+)"', pj.read_text(errors="replace"))
        if m and m.group(1).strip():
            return m.group(1).strip().rstrip("/")

    # fallback: conventional GitHub Pages URL derived from the deployed repo name
    du = proj / "frontend" / "dist" / "index.html"
    if du.exists():
        html = du.read_text(errors="ignore")
        m = re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', html, re.I)
        if m and "github.io" in m.group(1):
            return m.group(1).strip().rstrip("/")
    return ""


def write_readme(proj_dir: Path, brand: dict, link: str):
    (proj_dir / "README.md").write_text(
        f"""# {brand['name']}

{brand['tagline']}

- **Industry:** {brand['industry']}
- **Live link:** see `LIVE-LINK.txt` in this package

## Quick start
```
npm install
npm run dev
npm run build
```
""",
        encoding="utf-8",
    )


def write_link_txt(proj_dir: Path, link: str):
    content = f"LIVE LINK\n=========\n{link}\n" if link else "LIVE LINK\n=========\n(not deployed yet — run npm run dev locally)\n"
    (proj_dir / "LIVE-LINK.txt").write_text(content, encoding="utf-8")


def zip_project(src: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(src)
            z.write(f, f"{src.name}/{rel}")


def main() -> int:
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    made = 0
    for proj in sorted(projects):
        slug = proj.name
        brand = BRANDS.get(slug, BRANDS["build"])
        brand_slug = slugify(brand["name"])
        link = homepage_of(proj)

        dest = OUT / brand_slug
        shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True, exist_ok=True)

        dist = proj / "frontend" / "dist"
        if dist.exists():
            shutil.copytree(dist, dest / "dist", dirs_exist_ok=True)
        src_dir = proj / "frontend" / "src"
        if src_dir.exists():
            shutil.copytree(src_dir, dest / "src", dirs_exist_ok=True)
        write_readme(dest, brand, link)
        write_link_txt(dest, link)

        zip_path = OUT / f"{brand_slug}.zip"
        if zip_path.exists():
            zip_path.unlink()
        zip_project(dest, zip_path)
        made += 1
        print(f"  {brand_slug}.zip  {'link:' + link if link else '(no live link yet)'}")
    print("ZIPs created:", made)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())