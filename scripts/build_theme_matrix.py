"""Build the Template × Design-Style theme matrix (Part 1).

Writes the full matrix to registry/theme-matrix.json — the formal record of
every Template × Style variant, its preview path, and per-variant quality
gate. Idempotent, deterministic.

Usage:
    python scripts/build_theme_matrix.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ai-agent'))
sys.path.insert(0, str(ROOT))

from agent.theme_matrix import ThemeMatrixEngine
from utils.file_manager import FileManager

REG = ROOT / 'registry'


def main():
    engine = ThemeMatrixEngine(str(REG / 'templates.json'))
    matrix = engine.build_matrix()
    report = {
        'generator': 'theme-matrix-engine',
        'templates': len(engine.templates),
        'styles': len(engine.style_ids),
        'variants': len(matrix),
        'by_style': {},
        'matrix': matrix,
    }
    from collections import Counter
    c = Counter(r['style_id'] for r in matrix)
    report['by_style'] = dict(sorted(c.items()))
    FileManager.write_json(str(REG / 'theme-matrix.json'), report)
    print(f'BUILD_MATRIX_OK templates={len(engine.templates)} styles={len(engine.style_ids)} '
          f'variants={len(matrix)}')
    print('by_style:', dict(c))


if __name__ == '__main__':
    main()
