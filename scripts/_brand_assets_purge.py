"""Brand assets: recolor residual blue-family/gold hexes in public + dist SVG/JSON/txt assets
to each project's real brand/accent (from --t-primary/--t-accent), so OG/icon/illustration
assets are blue/gold-free and match the site identity. Overwrites in place (idempotent)."""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECTS = ROOT / 'generated-projects'

BLUES = ['#2563eb', '#1d4ed8', '#1e40af', '#3b82f6', '#0ea5e9', '#0284c7',
         '#0369a1', '#60a5fa', '#1e3a8a', '#172554', '#6366f1']
SLATE_NAVY = ['#0f172a', '#1e293b']
GOLDS = ['#b8860b', '#8b4513', '#daa520', '#a16207', '#b45309']
NEUTRAL_DARK = '#0e1116'
NEUTRAL_CARD = '#26292f'
EXT = {'.svg', '.json', '.txt'}


def brand_tokens(proj: pathlib.Path, progress: dict = None) -> tuple:
    brand = accent = None
    css = proj / 'frontend' / 'src' / 'index.css'
    if css.exists():
        t = css.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'--t-primary:\s*(#[0-9a-fA-F]{6})', t)
        if m:
            brand = m.group(1)
        m = re.search(r'--t-accent:\s*(#[0-9a-fA-F]{6})', t)
        if m:
            accent = m.group(1)
        if not brand:
            m = re.search(r'--t-brand:\s*(#[0-9a-fA-F]{6})', t)
            if m:
                brand = m.group(1)
    if not brand:
        theme = proj / 'frontend' / 'src' / 'lib' / 'theme.js'
        if theme.exists():
            t = theme.read_text(encoding='utf-8', errors='ignore')
            for key in ('--t-primary', '--t-brand'):
                m = re.search(re.escape(key) + r':\s*(#[0-9a-fA-F]{6})', t)
                if m:
                    brand = m.group(1)
                    break
    if not brand and progress:
        row = progress.get(proj.name)
        if row:
            brand = row.get('brand')
    return brand, accent


def recolour(text: str, brand: str, accent: str) -> str:
    for h in BLUES:
        text = re.sub(re.escape(h), brand, text, flags=re.I)
    for h in SLATE_NAVY:
        text = re.sub(re.escape(h), NEUTRAL_CARD if h == '#1e293b' else NEUTRAL_DARK, text, flags=re.I)
    for h in GOLDS:
        text = re.sub(re.escape(h), accent, text, flags=re.I)
    return text


def main() -> int:
    wanted = set(sys.argv[1:])
    progress = {}
    progress_file = PROJECTS / 'UNIQUE_RESTYLE_PROGRESS.json'
    if progress_file.exists():
        import json
        progress = {r['slug']: r for r in json.loads(progress_file.read_text(encoding='utf-8'))}
    changed = []
    for proj in sorted(PROJECTS.iterdir()):
        if not (proj / 'frontend').exists():
            continue
        if wanted and proj.name not in wanted:
            continue
        brand, accent = brand_tokens(proj, progress)
        if not brand:
            continue
        accent = accent or brand
        touched = 0
        for base in (proj / 'frontend' / 'public', proj / 'frontend' / 'dist'):
            if not base.exists():
                continue
            for f in base.rglob('*'):
                if not f.is_file() or f.suffix.lower() not in EXT:
                    continue
                try:
                    t = f.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                nt = recolour(t, brand, accent)
                if nt != t:
                    f.write_text(nt, encoding='utf-8')
                    touched += 1
        changed.append((proj.name, brand, accent, touched))
    print(f'projects recoloured: {len(changed)}')
    for name, brand, accent, touched in changed:
        print(f'  {name:<30} brand={brand} accent={accent} files={touched}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())