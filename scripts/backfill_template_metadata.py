"""Backfill template metadata (Part 2) onto registry/templates.json.

Idempotent enrichment: computes compatible_styles, sections_used,
conversion_optimized, complexity, industries_secondary and the auto-update
fields for every entry. Safe to re-run — only adds/updates, never deletes.
Mirrors scripts/backfill_template_metadata.py from the prompt spec.

Usage:
    python scripts/backfill_template_metadata.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ai-agent'))
sys.path.insert(0, str(ROOT))

from agent.theme_matrix import ThemeMatrixEngine

REG = ROOT / 'registry' / 'templates.json'


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'template'


def main():
    data = json.loads(Path(REG).read_text(encoding='utf-8'))
    engine = ThemeMatrixEngine(str(REG))
    for tpl in data:
        tpl['id'] = tpl.get('id') or slugify(tpl.get('name', ''))
        tpl['compatible_styles'] = engine.compatible_styles(tpl)
        tpl['sections_used'] = engine.sections_for(tpl)
        tpl['conversion_optimized'] = bool(tpl.get('conversion_optimized', tpl.get('rating', 0) >= 4.8))
        tpl.setdefault('quality_score', tpl.get('rating', 4.8))
        tpl.setdefault('complexity', 'medium')
        tpl.setdefault('industries_secondary', [])
        tpl['preview_screenshot'] = 'auto-generated per style variant'
        tpl['last_updated'] = 'auto'
    Path(REG).write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f'BACKFILL_META_OK templates={len(data)}')


if __name__ == '__main__':
    main()
