"""Package a template into a portable .lctemplate plugin archive (Part 6).

Produces a self-contained, installable template/style pack (WordPress-theme
spirit for LumicorePro's code-output model): manifest + template metadata +
the style token contents, zipped. Designed so power users/agencies can share
packs without touching core code.

Usage:
    python scripts/package_template.py --id restaurant-landing
    python scripts/package_template.py --all --out public/packs
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ai-agent'))
sys.path.insert(0, str(ROOT))

from agent.theme_matrix import ThemeMatrixEngine

REG = ROOT / 'registry'


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'template'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--id', default=None, help='template id to package')
    ap.add_argument('--all', action='store_true', help='package every template')
    ap.add_argument('--out', default=str(ROOT / 'public' / 'packs'))
    args = ap.parse_args()

    engine = ThemeMatrixEngine(str(REG / 'templates.json'))
    out = Path(args.out)
    made = []
    for tpl in engine.templates:
        if not args.all and tpl.get('id') not in ([args.id] if args.id else []):
            continue
        path = engine.package_template(tpl, str(out))
        made.append(path)
    if args.all:
        print(f'PACK_ALL_OK packaged={len(made)} -> {out}')
    else:
        print(f'PACK_OK {made[0] if made else "(no match)"}')


if __name__ == '__main__':
    main()
