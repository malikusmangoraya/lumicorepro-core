"""Style Wheel — generate 9 UI-style demo builds from one seed project.

Each style is a real Vite build reusing a single node_modules install, so
the whole wheel renders 9 distinct design languages with one dependency pass.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.pro_design import restyle_project  # noqa: E402
from agent.pro_design import UI_STYLE_DEFAULT, UI_STYLE_PALETTE, UI_STYLE_CSS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED = ROOT / 'generated-projects'
SEED = GENERATED / 'resupro-002'
WHEEL = GENERATED / 'ui-style-wheel'
STYLES = [
    'glassmorphism',
    'minimalist',
    'neobrutalism',
    'bento',
    'neumorphism',
    'flat',
    'claymorphism',
    'skeuomorphism',
    'dark',
]


def seed_frontend():
    """Copy the seed project's frontend into the wheel workspace (clean)."""
    if WHEEL.exists():
        shutil.rmtree(WHEEL)
    WHEEL.mkdir(parents=True)
    shutil.copytree(SEED / 'frontend', WHEEL / 'frontend',
                    ignore=shutil.ignore_patterns('node_modules', 'dist', '.git', 'package-lock.json'))
    # fresh lockfile + clean package.json so the pin-ensure step rewrites it
    (WHEEL / 'frontend' / 'package.json').unlink(missing_ok=True)
    # extra pages (About/Services/Contact) may be absent in seed; Home is enough


def build_style(style: str, index: int) -> bool:
    print(f'\n=== [{index}/9] {style} ===')
    ok = restyle_project(str(WHEEL), 'style-wheel-demo', style)
    if not ok:
        print('RESTYLE FAILED')
        return False
    r = subprocess.run(
        ['cmd', '/c', 'npm run build'],
        cwd=str(WHEEL / 'frontend'),
        capture_output=True, text=True, encoding='utf-8',
        timeout=600,
    )
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        return False
    dist = WHEEL / 'frontend' / 'dist'
    if not dist.exists():
        print('NO dist/ output')
        return False
    out = WHEEL / style
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(dist, out)
    print(f'BUILT → {out.relative_to(GENERATED)} ({len(list(out.rglob("*")))} files)')
    return True


def main():
    seed_frontend()
    print(f'Seed copied to {WHEEL / "frontend"}')
    # Regenerate the pinned package.json so npm doesn't walk up to repo root
    restyle_project(str(WHEEL), 'style-wheel-demo', UI_STYLE_DEFAULT)
    r = subprocess.run(
        ['cmd', '/c', 'npm install --no-audit --no-fund'],
        cwd=str(WHEEL / 'frontend'),
        capture_output=True, text=True, encoding='utf-8',
        timeout=1800,
    )
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:])
        sys.exit(2)
    print('npm install OK')

    results = {}
    for i, style in enumerate(STYLES, 1):
        results[style] = build_style(style, i)

    print('\n=== STYLE WHEEL RESULT ===')
    for style in STYLES:
        ok = results.get(style)
        print(f'{style:<16} {"OK" if ok else "FAIL":<6} {WHEEL / style if ok else ""}')


if __name__ == '__main__':
    main()