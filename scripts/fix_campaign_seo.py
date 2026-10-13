"""Repair the deployed campaign sites' SEO identity fields.

Every one of the 10 live campaign repos shipped with the same three defects
(found by scripts/audit_live_campaigns.py):
  1. og:image  -> truncated repo slug  e.g. github.io/ember/og-image.svg  (404)
  2. twitter:image -> invented domain e.g. https://ember-salt.com/...     (404)
  3. JSON-LD @id/url/logo -> that same invented domain, contradicting
     og:url/canonical so the entity had no resolvable identity

This applies the same rewrite the generator now uses
(international_pass1_global.rewrite_seo_html) to every index.html in a
project, whichever layout it has:
  - cloned gh-pages artifact  -> <slug>/index.html
  - full local source tree    -> <slug>/frontend/{index.html,dist/index.html}

Existing hreflang languages are preserved rather than re-guessed.

Usage:
  python scripts/fix_campaign_seo.py                      # all campaigns, dry run
  python scripts/fix_campaign_seo.py --write              # apply
  python scripts/fix_campaign_seo.py --write ember-salt   # apply to one
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from international_pass1_global import rewrite_seo_html  # noqa: E402

OWNER = "malikusmangoraya"
ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"
# Campaigns moved here when the sell-today storefronts became first-class
# products; the repair tool resolves both homes so scope never drifts.
SELL_TODAY = ROOT / "products" / "sell-today"


def resolve_project_dir(slug: str) -> Optional[Path]:
    """Project home for a campaign slug: generated-projects/ or sell-today/."""
    for base in (PROJECTS, SELL_TODAY):
        candidate = base / slug
        if candidate.is_dir():
            return candidate
    return None

CAMPAIGNS = [
    "aurelia-estates",
    "aurum-fitness",
    "ember-salt",
    "maison-noir",
    "meridian-capital",
    "nuage-events",
    "prestige-studio",
    "saffron-voyage",
    "studio-lumen",
    "voltus-atelier",
]

# GitHub project Pages mount each campaign under /<slug>/, but the file lives at
# the repo root, so the prefix has to come off before checking the filesystem.
PROJECT_PREFIXES = set(CAMPAIGNS)


def strip_project_prefix(rel_path: str) -> str:
    """`/ember/og-image.svg` on a campaign that is really `/ember-salt/...`
    is a truncated slug, not a directory: it has to lose its first segment."""
    parts = [p for p in rel_path.split("/") if p]
    if len(parts) > 1 and parts[0] in PROJECT_PREFIXES:
        return "/".join(parts[1:])
    return "/".join(parts)

INDEX_CANDIDATES = (
    "index.html",
    "frontend/index.html",
    "frontend/dist/index.html",
    "dist/index.html",
)


def base_url(slug: str) -> str:
    return f"https://{OWNER}.github.io/{slug}"


def existing_langs(text: str) -> list[str]:
    """Reuse the hreflang set already in the document so nothing is lost."""
    found = re.findall(r'hreflang="([a-zA-Z-]+)"', text)
    found = [lg for lg in dict.fromkeys(found) if lg != "x-default"]
    return found


def locale_langs(slug: str) -> list[str]:
    project = resolve_project_dir(slug)
    loc = project / "frontend" / "src" / "i18n" / "locales" if project else None
    if loc is not None and loc.is_dir():
        langs = sorted(p.stem for p in loc.glob("*.json"))
        if langs:
            return langs
    return []


def seo_problems(text: str, url: str) -> list[str]:
    """Every SEO identity field in `text` that does not point at `url`."""
    problems = []

    def grab(pattern):
        m = re.search(pattern, text, re.I | re.S)
        return m.group(1) if m else None

    for label, value in (
        ("og:url", grab(r'<meta\s+property="og:url"\s+content="([^"]+)"')),
        ("canonical", grab(r'<link\s+rel="canonical"\s+href="([^"]+)"')),
    ):
        if value and value.rstrip("/") != url.rstrip("/"):
            problems.append(f"{label} -> {value}")

    for label, value in (
        ("og:image", grab(r'<meta\s+property="og:image"\s+content="([^"]+)"')),
        ("twitter:image", grab(r'<meta\s+name="twitter:image"\s+content="([^"]+)"')),
    ):
        if value and not value.startswith(url + "/"):
            problems.append(f"{label} -> {value}")

    for key, value in re.findall(r'("(?:@id|url)"\s*:\s*")([^"]*)"', text):
        if value.rstrip("/") != url and not value.rstrip("/").startswith(url + "/"):
            problems.append(f"JSON-LD {key.strip().strip(chr(34))} -> {value}")

    return problems


def audit_file(path: Path, url: str) -> tuple[bool, list[str], list[str]]:
    """Return (needs_fix, defects_found, residual_unfixed) without writing."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    langs = existing_langs(text) or locale_langs(path.parts[-3])
    fixed = rewrite_seo_html(text, url, langs)
    defects = seo_problems(text, url)
    # the rewriter is only trustworthy if nothing survives it
    residual = seo_problems(fixed, url)
    return fixed != text, defects, residual


def missing_assets(path: Path, url: str) -> list[str]:
    """SEO metadata is only useful if the file it advertises exists.

    The 3 locally-held projects keep sources in `frontend/` and ship
    `frontend/dist/`, and Vite serves static files from `frontend/public/`
    during dev but copies them into `dist/` for a build — so a source
    `index.html` legitimately resolves `og-image.svg` against `public/`.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    served_from = path.parent
    search_roots = [served_from]
    if served_from.name == "frontend":
        search_roots.append(served_from / "public")

    missing = []
    for name, pattern in (
        ("og:image", r'<meta\s+property="og:image"\s+content="([^"]+)"'),
        ("twitter:image", r'<meta\s+name="twitter:image"\s+content="([^"]+)"'),
        ("favicon", r'<link\s+rel="icon"[^>]*href="([^"]+)"'),
    ):
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        value = match.group(1)
        if value.startswith(("http://", "https://")):
            # the Pages URL carries the project prefix; the repo root is where
            # the file actually lives
            rel = strip_project_prefix(urlsplit(value).path)
        else:
            rel = value[2:] if value.startswith("./") else value.lstrip("/")
        if not rel:
            continue
        if not any((root / rel).is_file() for root in search_roots):
            missing.append(f"{name} -> {value} (expected {rel} beside {served_from.as_posix()})")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slugs", nargs="*", help="campaign slugs (default: all)")
    parser.add_argument("--write", action="store_true", help="write changes")
    args = parser.parse_args()

    targets = args.slugs or CAMPAIGNS
    changed_files = 0
    pending = 0
    clean_projects = 0
    missing_projects = []
    total_defects = 0
    residual_total = 0
    missing_assets_total = 0

    for slug in targets:
        project = resolve_project_dir(slug)
        if project is None:
            missing_projects.append(slug)
            print(f"[SKIP] {slug}: not present locally")
            continue

        url = base_url(slug)
        files = [project / c for c in INDEX_CANDIDATES if (project / c).is_file()]
        if not files:
            print(f"[SKIP] {slug}: no index.html found")
            continue

        project_ok = True
        for path in files:
            rel = path.relative_to(project).as_posix()
            try:
                needs_fix, defects, residual = audit_file(path, url)
            except Exception as exc:
                print(f"[ERROR] {slug}/{rel}: {exc}")
                project_ok = False
                continue

            total_defects += len(defects)

            # A correct URL to a file that was never generated is still a broken
            # preview, so asset presence is part of "fixed", not a nicety.
            for problem in missing_assets(path, url):
                project_ok = False
                missing_assets_total += 1
                print(f"[ASSET] {slug}/{rel}: {problem}")

            if residual:
                # the rewriter could not repair these — real blocker, not cosmetic
                project_ok = False
                residual_total += len(residual)
                for problem in residual:
                    print(f"[STUCK] {slug}/{rel}: {problem} (rewriter could not fix)")

            if not needs_fix and not defects:
                if project_ok:
                    print(f"[OK]   {slug}/{rel}")
                continue

            project_ok = False
            for problem in defects:
                print(f"[FIX]  {slug}/{rel}: {problem}")
            if args.write:
                text = path.read_text(encoding="utf-8", errors="ignore")
                langs = existing_langs(text) or locale_langs(slug)
                path.write_text(rewrite_seo_html(text, url, langs), encoding="utf-8")
                changed_files += 1
                print(f"[WROTE] {slug}/{rel}  ({len(defects)} defect(s) fixed)")
            else:
                pending += 1
                print(f"[DRY]  {slug}/{rel} would be rewritten ({len(defects)} defect(s))")

        if project_ok:
            clean_projects += 1

    print()
    print(f"mode={'write' if args.write else 'dry-run'} | files rewritten={changed_files} "
          f"| pending={pending} | defects found={total_defects} "
          f"| residual={residual_total} | missing assets={missing_assets_total} "
          f"| clean projects={clean_projects}/{len(targets)} "
          f"| missing={len(missing_projects)}")
    if residual_total:
        print("RESULT: FAIL — some fields the rewriter cannot repair; inspect [STUCK] lines")
        return 1
    if missing_assets_total:
        print("RESULT: FAIL — metadata points at files that do not exist; inspect [ASSET] lines")
        return 1
    if not args.write and pending == 0:
        print("nothing to do")
    return 0


if __name__ == "__main__":
    sys.exit(main())