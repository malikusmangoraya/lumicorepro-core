"""Fill LIVE-LINK.txt (inside zips) with each project's real live URL.

The canonical live link is discovered per-project from its own build artifacts
(og:url / index.html) so the link lives ONLY inside the ZIP package.
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

URL_RE = re.compile(r"https?://[^\s'\"><)]+")
LIVE_URL_TXT = GEN / "ai-content-studio_LIVE_URL.txt"

# Repos that hold ONLY the last thing deployed there (shared/legacy) — must
# never be claimed as a per-website link for a specific brand.
DEFAULT_REPOS = {"build", "rest", "style"}
# Campaign projects verified on their own unique, brand-slug GitHub Pages repo
# (project dir -> repo name on malikusmangoraya.github.io).
VERIFIED = {
    "aurelia-estates": "aurelia",
    "aurum-fitness": "aurum",
    "ember-salt": "ember",
    "maison-noir": "maison",
    "meridian-capital": "meridian",
    "nuage-events": "nuage",
    "prestige-studio": "prestige",
    "saffron-voyage": "saffron",
    "studio-lumen": "studio",
    "voltus-atelier": "voltus",
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def project_link(proj: Path) -> str:
    """Return the canonical live link for a project (None if none real)."""
    bad = ("example.com", "placeholder", "your-site", "yourdomain", "localhost")
    # 1) per-project LIVE_URL txt
    for f in proj.rglob("*LIVE_URL*.txt"):
        try:
            t = f.read_text(errors="ignore").strip()
            for u in URL_RE.findall(t):
                if ("github.io" in u or "pages.dev" in u) and not any(b in u for b in ("example", "placeholder", "your-")):
                    return u.rstrip("/")
        except Exception:
            continue
    # 2) frontend/index.html og:url or appli github.io
    for cand in ("frontend/dist/index.html", "frontend/index.html"):
        f = proj / cand
        if f.exists():
            t = f.read_text(errors="ignore")
            m = re.search(r'property="og:url"\s+content="([^"]+)"', t)
            if m and not any(b in m.group(1) for b in bad):
                return m.group(1).rstrip("/")
            for u in URL_RE.findall(t):
                if "github.io" in u and "og" not in u and not any(b in u for b in bad):
                    return u.rstrip("/")
    return ""


def rebuild_zip(dest: Path, zip_path: Path):
    src = dest
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                z.write(f, f"{src.name}/{f.relative_to(src)}")


def main() -> int:
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    mapped = 0
    for proj in sorted(projects):
        brand = BRANDS.get(proj.name, BRANDS["build"])
        brand_slug = slugify(brand["name"])
        link = project_link(proj)
        if link:
            repo = link.rstrip("/").split("/")[-1]
            if repo in DEFAULT_REPOS or repo != brand_slug:
                link = ""
        dest = OUT / brand_slug
        if not dest.exists():
            print(f"  !! {brand_slug}: delivery folder missing")
            continue
        content = f"LIVE LINK\n=========\n{link}\n" if link else "LIVE LINK\n=========\n(not deployed yet — run npm run dev locally)\n"
        (dest / "LIVE-LINK.txt").write_text(content, encoding="utf-8")
        zip_path = OUT / f"{brand_slug}.zip"
        if zip_path.exists():
            zip_path.unlink()
        rebuild_zip(dest, zip_path)
        mapped += 1
        print(f"  {brand_slug}.zip  link={link}" if link else f"  {brand_slug}.zip  (no link)")
    print("ZIPs with links:", mapped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())