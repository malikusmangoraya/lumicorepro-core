"""Pass 2 — international gap fixes on top of internationalize_all.py.

Fixes identified by INTERNATIONAL_AUDIT.md:
  A. App.jsx routing: projects whose auto-router maps every path to <Home /> (or
     that gained Login/Register pages without routes) get the full lazy route map.
  B. Motion: inject the lumi-motion layer into every project that lacks it
     (the 10 campaigns already ship it).
  C. SEO: add <meta name="description"> + Open Graph tags to index.html where
     they are missing, linked to the project's own og-image.svg.
Rebuilds every frontend whose source changed.
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / 'generated-projects'
SCRIPTS = ROOT / 'scripts'

spec = importlib.util.spec_from_file_location('iai', SCRIPTS / 'internationalize_all.py')
iai = importlib.util.module_from_spec(spec)
sys.modules['iai'] = spec
spec.loader.exec_module(iai)

sys.path.insert(0, str(ROOT / 'ai-agent'))
from agent.extensions.animation_injector import inject_motion_layer  # noqa: E402

BRAND_TITLES = {
    'aurelia-estates': 'Aurelia Estates',
    'maison-noir': 'Maison Noir',
    'ember-salt': 'Ember & Salt',
    'saffron-voyage': 'Saffron Voyage',
    'prestige-studio': 'Prestige',
    'meridian-capital': 'Meridian Capital',
    'voltus-atelier': 'Voltus Atelier',
    'aurum-fitness': 'Aurum Fitness',
    'studio-lumen': 'Studio Lumen',
    'nuage-events': 'Nuage Events',
}

STANDARD_PAGES = ['Home', 'About', 'Services', 'Pricing', 'Contact', 'Login', 'Register']
ROUTE_FOR = {
    'About': '/about', 'Services': '/services', 'Pricing': '/pricing',
    'Contact': '/contact', 'Login': '/login', 'Register': '/register',
}


def brand_name(slug: str) -> str:
    if slug in BRAND_TITLES:
        return BRAND_TITLES[slug]
    return slug.replace('-', ' ').title()


def ensure_pages(fe, brand_info) -> list:
    pages = fe / 'src' / 'pages'
    pages.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in pages.glob('*.jsx')}
    created = []
    for name in STANDARD_PAGES:
        if name in existing:
            continue
        if name == 'Home':
            continue  # never auto-create Home without bespoke source
        template = {
            'About': iai.ABOUT_PAGE, 'Services': iai.SERVICES_PAGE,
            'Pricing': iai.PRICING_PAGE, 'Contact': iai.CONTACT_PAGE,
            'Login': iai.LOGIN_PAGE, 'Register': iai.REGISTER_PAGE,
        }[name]
        content = iai._render(template, ABOUT_TEXT=brand_info.get('about_text', ''))
        iai._write(pages / f'{name}.jsx', content)
        created.append(name)
    return created


def fix_routing(fe, slug) -> bool:
    """Return True if App.jsx (or pages) changed."""
    pages_dir = fe / 'src' / 'pages'
    app = fe / 'src' / 'App.jsx'
    if not app.exists() or not pages_dir.exists():
        return False
    app_txt = iai._read(app)
    route_els = set(re.findall(r'element={<([A-Za-z]+)\s*/>}', app_txt))
    html_homes = app_txt.count('element={<Home />}')
    changed = False

    # Case A: placeholder router — EVERY route renders <Home /> (e.g. a router
    # that lists /about /services /contact but maps each to the home page).
    # Guarded to boutique routers (several paths, all -> Home) so real apps that
    # route /checkout /admin /login to real pages are never touched.
    if route_els == {'Home'} and html_homes >= 2 and all((pages_dir / f'{p}.jsx').exists() for p in STANDARD_PAGES):
        created = ensure_pages(fe, iai._load_brand_info(slug and GEN / slug))
        iai._write(app, iai.FULL_APP_JSX)
        for lib in (fe / 'src' / 'lib' / 'theme.js',):
            if not lib.exists():
                iai._write(lib, '// theme loader\n')
        if not (fe / 'src' / 'lib' / 'AppProviders.jsx').exists():
            iai._write(fe / 'src' / 'lib' / 'AppProviders.jsx', iai.APPPROVIDERS_JSX)
        print(f'  {slug}: [A] full routing applied' + (f' (+{len(created)} pages)' if created else ''))
        return True

    # Case B: distinct per-route app missing routes for pages that got injected.
    if html_homes <= 1 and '<Routes>' in app_txt:
        missing = [p for p in STANDARD_PAGES if p != 'Home'
                   and (pages_dir / f'{p}.jsx').exists()
                   and f"lazy(() => import('./pages/{p}')" not in app_txt
                   and f'path="{ROUTE_FOR[p]}"' not in app_txt]
        if missing:
            lazy_lines = '\n'.join(
                f"const {p} = lazy(() => import('./pages/{p}'));" for p in missing
            )
            route_lines = '\n            '.join(
                '<Route path="' + ROUTE_FOR[p] + '" element={' + '<' + p + ' />} />' for p in missing
            )
            if 'lazy(' in app_txt:
                app_txt = app_txt.replace(
                    'const Home = lazy(() => import(\'./pages/Home\'));',
                    'const Home = lazy(() => import(\'./pages/Home\'));\n' + lazy_lines, 1,
                ) if 'const Home = lazy' in app_txt else app_txt
                if 'const Home = lazy' not in app_txt:
                    anchor = re.search(r'^const \w+ = lazy\([^\n]*\n', app_txt, re.M)
                    if anchor:
                        app_txt = app_txt[:anchor.end()] + lazy_lines + '\n' + app_txt[anchor.end():]
            app_txt = app_txt.replace('</Routes>', '            ' + route_lines + '\n          </Routes>', 1)
            iai._write(app, app_txt)
            print(f'  {slug}: [B] added routes for {", ".join(missing)}')
            return True
    return changed


def fix_seo(fe, slug) -> bool:
    index_html = fe / 'index.html'
    if not index_html.exists():
        return False
    html = index_html.read_text(encoding='utf-8', errors='ignore')
    name = brand_name(slug)
    desc = f'{name} — premium web experience. Explore collections, services, and pricing crafted with world-class design.'
    inject = []
    if 'name="description"' not in html and "name='description'" not in html:
        inject.append(f'<meta name="description" content="{desc}" />')
    og_missing = [t for t in ('og:title', 'og:description', 'og:image', 'og:type') if f'{t}' not in html]
    if og_missing or ('og:image' not in html and 'og:image' not in html):
        if 'og:title' not in html:
            inject.append(f'<meta property="og:title" content="{name}" />')
        if 'og:description' not in html:
            inject.append(f'<meta property="og:description" content="{desc}" />')
        if 'og:image' not in html:
            inject.append('<meta property="og:image" content="/og-image.svg" />')
        if 'og:type' not in html:
            inject.append('<meta property="og:type" content="website" />')
    if not inject:
        return False
    marker = re.search(r'<meta charset="[^"]*"[^>]*/?>', html)
    anchor = marker.end() if marker else html.find('</head>')
    html = html[:anchor] + '\n    ' + inject[0] + '\n    '.join(inject[1:]) + '\n' + html[anchor:]
    index_html.write_text(html, encoding='utf-8')
    print(f'  {slug}: [C] SEO meta added ({len(inject)} tag(s))')
    return True


def main():
    changed = {}
    for proj in sorted(GEN.iterdir()):
        if not proj.is_dir():
            continue
        fe = proj / 'frontend'
        if not (fe / 'src' / 'main.jsx').exists():
            continue
        slug = proj.name
        states = []
        try:
            states.append(('routing', fix_routing(fe, slug)))
            states.append(('seo', fix_seo(fe, slug)))

            css = fe / 'src' / 'index.css'
            has_motion = css.exists() and (
                'lumi-motion-injected' in css.read_text(encoding='utf-8', errors='ignore')
                or '/* ===== lumi-motion' in css.read_text(encoding='utf-8', errors='ignore')
            )
            if not has_motion:
                r = inject_motion_layer(str(proj), intensity='high', write_report=True)
                states.append(('motion', r.get('status') == 'injected'))
                print(f'  {slug}: [M] motion {r.get("status")}')
            touched = any(ok for _, ok in states)
            if touched:
                changed[slug] = True
        except Exception as exc:  # noqa: BLE001
            print(f'  {slug}: ERROR {exc}')

    print(f'\ntouched {len(changed)} projects; rebuilding…')
    for slug in sorted(changed):
        fe = GEN / slug / 'frontend'
        if not (fe / 'package.json').exists():
            continue
        import os
        import subprocess
        cmd = 'npm run build' if os.name == 'nt' else ['npm', 'run', 'build']
        r = subprocess.run(cmd, cwd=str(fe), shell=False if os.name != 'nt' else True,
                           capture_output=True, text=True, timeout=180)
        print(f'  {slug}: {"OK" if r.returncode == 0 else "FAILED"}')
        if r.returncode != 0:
            print('    ' + r.stderr[-600:].replace('\n', '\n    '))


if __name__ == '__main__':
    main()