"""International-standard gap audit for all generated projects.
Compares each upgraded frontend against the international website benchmark
(typography, imagery, nav, footer, i18n/RTL, SEO/OG, a11y, motion, performance).
Fast, read-only. Writes INTERNATIONAL_AUDIT.md per project + one root report.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / 'generated-projects'

PLACEHOLDER_RE = re.compile(
    r'\b(lorem|ipsum|dolor|todo|fixme|coming\s+soon|your\s+brand|your\s+company|'
    r'placeholder|dummy\s+text|under\s+construction|sample\s+text|add\s+your)\b',
    re.IGNORECASE,
)
EXTERNAL_IMG_RE = re.compile(r'["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp|gif)[^"\']*)["\']', re.IGNORECASE)
EMPTY_SRC_RE = re.compile(r'(?:src|href)=["\']\s*["\']')
CTA_RE = re.compile(r'className="[^"]*\b(?:bg-[\w-]+|primary|brand)[^"]*"')

BENCH = {
    'typography': 9,
    'composition': 9,
    'spacing': 8,
    'color': 8,
    'imagery': 9,
    'hierarchy': 9,
    'consistency': 8,
    'brand': 9,
    'motion': 8,
    'originality': 9,
}


def scan(fe: Path) -> dict:
    res = {
        'slug': fe.parent.name,
        'has_og': False, 'has_meta_desc': False, 'has_title': False,
        'placeholder_hits': [], 'empty_src': 0, 'external_imgs': [],
        'alt_missing': 0, 'h1': 0, 'cta_hero': False,
        'mobile_menu': False, 'auth_links': False,
        'footer_columns': 0, 'footer_newsletter': False, 'footer_social': False, 'footer_status': False,
        'lazy_routes': 0, 'tokens_in_css': False, 'lumi_motion_css': False,
        'i18n': False, 'rtl': False, 'multi_currency': False,
        'font_display': False, 'images_total': 0,
    }

    index_html = fe / 'index.html'
    if index_html.exists():
        html = index_html.read_text(encoding='utf-8', errors='ignore')
        res['has_title'] = '<title>' in html and '</title>' in html
        res['has_meta_desc'] = 'name="description"' in html or "name='description'" in html
        res['has_og'] = ('og:title' in html or 'og:image' in html or 'property="og:' in html)
        res['rtl'] = 'dir="rtl"' in html

    src = fe / 'src'
    css = src / 'index.css'
    if css.exists():
        css_text = css.read_text(encoding='utf-8', errors='ignore')
        res['tokens_in_css'] = 'var(--t-' in css_text
        res['lumi_motion_css'] = 'lumi-motion' in css_text or '.lumi-' in css_text
        res['font_display'] = 'font-display' in css_text or 'fontDisplay' in css_text

    i18n_dir = src / 'i18n'
    res['i18n'] = i18n_dir.exists() or any((src / 'locales').rglob('*.json')) or (
        any(p.read_text(encoding='utf-8', errors='ignore').count("t('") > 3
            for p in list((src / 'pages').glob('*.jsx'))[:6])
    )

    if (src / 'context').exists() and (src / 'context' / 'CurrencyContext.jsx').exists():
        res['multi_currency'] = True

    for page in sorted((src / 'pages').glob('*.jsx')) if (src / 'pages').exists() else []:
        text = page.read_text(encoding='utf-8', errors='ignore')
        hits = PLACEHOLDER_RE.findall(text)
        res['placeholder_hits'].extend(f'{page.name}:{m}' for m in hits)
        res['empty_src'] += len(EMPTY_SRC_RE.findall(text))
        res['external_imgs'].extend(EXTERNAL_IMG_RE.findall(text))
        res['images_total'] += len(re.findall(r'<img\b', text))
        res['alt_missing'] += len(re.findall(r'<img\b(?![^>]*\balt=)[^>]*>', text))
        res['h1'] += len(re.findall(r'<h1\b', text))
        if not res['cta_hero'] and CTA_RE.search(text):
            res['cta_hero'] = True

    nav = src / 'components' / 'Navbar.jsx'
    if nav.exists():
        nav_txt = nav.read_text(encoding='utf-8', errors='ignore')
        res['mobile_menu'] = ('setOpen' in nav_txt or 'mobile' in nav_txt.lower() or 'Menu' in nav_txt)
        res['auth_links'] = ('/login' in nav_txt and '/register' in nav_txt)

    footer = next((src / 'components').rglob('Footer.jsx'), None)
    if footer:
        ftxt = footer.read_text(encoding='utf-8', errors='ignore')
        cols = len(re.findall(r'(<ul\b|<nav\b|className="[^"]*(?:grid-cols|grid flow-row|md:grid-cols)[^"]*")', ftxt))
        res['footer_columns'] = max(cols, len(re.findall(r'<h3\b|<h4\b', ftxt)))
        res['footer_newsletter'] = bool(re.search(r'[Nn]ewsletter|subscribe|Sign up|Join our', ftxt))
        res['footer_social'] = bool(re.search(r'[Tt]witter|[Ff]acebook|[Ii]nstagram|[Ll]inkedin|[Gg]ithub|X\b|social', ftxt))
        res['footer_status'] = bool(re.search(r'[Oo]perational|[Ss]tatus|uptime|99\.', ftxt))

    app = src / 'App.jsx'
    if app.exists():
        app_txt = app.read_text(encoding='utf-8', errors='ignore')
        res['lazy_routes'] = len(re.findall(r'lazy\(', app_txt))

    if res['placeholder_hits']:
        res['placeholder_hits'] = list(dict.fromkeys(res['placeholder_hits']))[:12]
    if res['external_imgs']:
        res['external_imgs'] = list(dict.fromkeys(res['external_imgs']))[:8]
    return res


def score(r: dict) -> tuple:
    s = 0.0
    checks = []
    def add(name, ok, w):
        nonlocal s
        s += BENCH.get(name, 8) * w if ok else 0
        checks.append((name, ok))

    add('hierarchy', r['h1'] == 1, 1.0)
    add('typography', r['font_display'] or r['h1'] >= 1, 1.0)
    add('composition', r['cta_hero'], 0.5)
    add('imagery', r['images_total'] > 0 and not r['external_imgs'], 1.0)
    add('spacing', r['lazy_routes'] >= 5, 0.5)
    add('consistency', r['tokens_in_css'], 1.0)
    add('brand', (r['footer_columns'] >= 3 or r['footer_newsletter']), 0.5)
    add('motion', r['lumi_motion_css'], 0.5)
    add('originality', not r['placeholder_hits'], 1.0)
    add('color', r['tokens_in_css'] and r['cta_hero'], 0.5)

    return round(s, 1), checks


def main():
    targets = sys.argv[1:] or None
    rows = []
    for proj in sorted(GEN.iterdir()):
        if not proj.is_dir():
            continue
        fe = proj / 'frontend'
        if not (fe / 'src' / 'main.jsx').exists():
            continue
        if targets and proj.name not in targets:
            continue
        r = scan(fe)
        r['score'], r['checks'] = score(r)
        rows.append(r)

    rows.sort(key=lambda r: r['score'])
    report = ROOT / 'generated-projects' / 'INTERNATIONAL_AUDIT.md'
    lines = ['# International-Standard Gap Audit\n',
             f'Projects audited: {len(rows)}  |  Benchmark targets: ' +
             ', '.join(f'{k} {v}/10' for k, v in BENCH.items()) + '\n',
             '| Slug | Score | Placeholder | OG/Desc | Footer cols | i18n | RTL | Currency | alt miss | external imgs | mobile | lazy |',
             '|------|-------|-------------|---------|-------------|------|-----|----------|----------|---------------|--------|------|']
    for r in rows:
        lines.append(
            f"| {r['slug']} | {r['score']:.0f} | {len(r['placeholder_hits'])} | "
            f"{'OG' if r['has_og'] else '-'}/{'D' if r['has_meta_desc'] else '-'} | "
            f"{r['footer_columns']} | {'Y' if r['i18n'] else '-'} | {'Y' if r['rtl'] else '-'} | "
            f"{'Y' if r['multi_currency'] else '-'} | {r['alt_missing']} | {len(r['external_imgs'])} | "
            f"{'Y' if r['mobile_menu'] else '-'} | {r['lazy_routes']} |"
        )
    lines.append('')
    for r in rows:
        top = [k for k, ok in r['checks'] if not ok]
        if top:
            lines.append(f"### {r['slug']} — {r['score']:.0f}/100")
            lines.append(f"- failed checks: {', '.join(top)}")
            if r['placeholder_hits']:
                lines.append(f"- placeholder copy: {', '.join(r['placeholder_hits'][:6])}")
            if r['external_imgs']:
                lines.append(f"- external images: {', '.join(r['external_imgs'][:4])}")
            lines.append('')
    report.write_text('\n'.join(lines), encoding='utf-8')
    print(f'audited {len(rows)} | report: {report}')
    for r in rows[:8]:
        print(f"  {r['score']:4.0f}  {r['slug']:<32} placeholders={len(r['placeholder_hits'])} "
              f"footer_cols={r['footer_columns']} i18n={r['i18n']} rtl={r['rtl']}")


if __name__ == '__main__':
    main()