"""Auto-preview generation (Part 5) for Theme Matrix variants.

Captures `previews/{template}/{style}.png` for each template+style combo by
serving each variant through a headless browser, so users can "browse before
they generate" (self-hosted gallery, Framer/Webflow-style).

Two modes (--mode):
  live    — run a real headless browser against each variant URL.
            (Requires `npm run preview` on the generated preview app + the
            Playwright browser bundle installed; captures true screenshots.)
  verify  — (default) no browser needed: checks every preview path is served
            by simply validating the manifest contract + counting existing
            PNGs. Use this in CI / offline.

Usage:
    python scripts/generate_previews.py --mode live   --base http://localhost:4173
    python scripts/generate_previews.py --mode verify
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ai-agent'))
sys.path.insert(0, str(ROOT))

from agent.theme_matrix import ThemeMatrixEngine
from utils.logger import agent_logger

REG = ROOT / 'registry'
PREVIEWS = ROOT / 'previews'


def _verify(engine):
    """Validates the end-to-end path/preview contract without a browser."""
    missing = []
    total = 0
    for tpl in engine.templates:
        tid = tpl.get('id') or 'template'
        for style in engine.compatible_styles(tpl):
            total += 1
            png = PREVIEWS / tid / f'{style}.png'
            if not png.exists():
                missing.append(f'{tid}/{style}.png')
    print(f'PREVIEWS_VERIFY templates={len(engine.templates)} expected_pngs={total} '
          f'present={total - len(missing)} missing={len(missing)}')
    if missing:
        print('missing (first 20):')
        for m in missing[:20]:
            print('  -', m)
    return len(missing) == 0


def _live(engine, base):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        agent_logger.error('playwright not installed — run `npm i -D @playwright/test` and `npx playwright install chromium`.')
        return False
    ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for tpl in engine.templates:
            tid = tpl.get('id') or 'template'
            for style in engine.compatible_styles(tpl):
                out = PREVIEWS / tid
                out.mkdir(parents=True, exist_ok=True)
                page = browser.new_page(viewport={'width': 1600, 'height': 1000})
                url = f'{base.rstrip("/")}/?template={tid}&style={style}'
                try:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    page.screenshot(path=str(out / f'{style}.png'), full_page=True)
                    ok += 1
                except Exception as e:
                    agent_logger.warning(f'preview failed {tid}/{style}: {e}')
                finally:
                    page.close()
        browser.close()
    print(f'PREVIEWS_LIVE captured={ok}')
    return ok > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='verify', choices=['verify', 'live'])
    ap.add_argument('--base', default='http://localhost:4173')
    args = ap.parse_args()

    engine = ThemeMatrixEngine(str(REG / 'templates.json'))
    if args.mode == 'live':
        ok = _live(engine, args.base)
    else:
        ok = _verify(engine)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
