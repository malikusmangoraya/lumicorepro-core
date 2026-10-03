"""Reconstruct canonical full routes for the 10 full-stack campaigns.

The pass-2 Case-A fix wrongly replaced campaign App.jsx, and zip-based restore
brought back a STALE pre-fullstack App. This repairs each campaign's App.jsx
in place: it keeps the project-specific shell (AppProviders, MotionCanvas,
Loader, cls-reserve, basename) and rebuilds the lazy imports + <Routes> block
from the pages that actually exist (Home + About/Services/Pricing/Contact/
Login/Register + Checkout + Admin).
"""
import re
from pathlib import Path

GEN = Path('generated-projects')
CAMPAIGNS = [
    'aurelia-estates', 'maison-noir', 'ember-salt', 'saffron-voyage',
    'prestige-studio', 'meridian-capital', 'voltus-atelier',
    'aurum-fitness', 'studio-lumen', 'nuage-events',
]


def repair(fe: Path) -> list:
    app = fe / 'src' / 'App.jsx'
    pages_dir = fe / 'src' / 'pages'
    if not app.exists():
        return ['no App.jsx']
    txt = app.read_text(encoding='utf-8', errors='ignore')

    existing_pages = sorted(p.stem for p in pages_dir.glob('*.jsx')) if pages_dir.exists() else []
    routable = ['Home', 'About', 'Services', 'Pricing', 'Contact', 'Login', 'Register', 'Checkout', 'Admin']
    routable = [p for p in routable if p in existing_pages]
    positions = ['Checkout', 'Admin']  # appended after standard set

    lazy_re = re.compile(r"const (\w+) = lazy\(\(\) => import\('\./pages/(\w+)'\)\);")
    existing_lazy = {m.group(1): m.group(2) for m in lazy_re.finditer(txt)}
    wanted = {p: p for p in routable}
    wanted.update({p: p for p in routable})

    # normalize page->const name mapping (page stems are PascalCase)
    missing_lazy = [p for p in routable if p not in existing_lazy.values()]
    if missing_lazy:
        block = '\n'.join(f"const {p} = lazy(() => import('./pages/{p}'));" for p in missing_lazy)
        last_lazy = None
        idx = None
        for m in lazy_re.finditer(txt):
            last_lazy = m
        if last_lazy:
            idx = last_lazy.end()
        else:
            idx = txt.find("function Loader")
        separator = "\n" if idx is not None else ""
        txt = txt[:idx] + separator + block + txt[idx:]

    # Rebuild the <Routes> block: keep existing custom routes, then enforce all routable.
    routes_start = txt.find('<Routes>')
    routes_end = txt.find('</Routes>')
    if routes_start == -1 or routes_end == -1:
        return ['no <Routes> block']
    inner = txt[routes_start + len('<Routes>'):routes_end]
    existing_routes = re.findall(r'<Route path="([^"]+)" element=\{<(\w+)\s*/>}', inner)
    kept = {}
    for path, comp in existing_routes:
        if comp in existing_pages and path not in ('/*', '*'):
            kept[comp] = path
    route_lines = []
    # build final route set (prefer existing custom paths, else default)
    final = []
    added = set()
    for p in routable:
        path = kept.get(p, '/' if p == 'Home' else '/' + p.lower())
        if path in ('/',) and p == 'Home':
            final.append(f'<Route path="/" element={{<{p} />}} />')
        else:
            final.append(f'<Route path="{path}" element={{<{p} />}} />')
        added.add(p)
    if '*' not in kept.values() and 'Home' in routable:
        final.append('<Route path="*" element={<Home />} />')

    new_inner = '\n            '.join(final)
    txt = txt[:routes_start + len('<Routes>')] + '\n            ' + new_inner + '\n          ' + txt[routes_end:]
    app.write_text(txt, encoding='utf-8')
    return routable


def main():
    for slug in CAMPAIGNS:
        fe = GEN / slug / 'frontend'
        res = repair(fe)
        print(f'{slug}: routes=[{", ".join(res)}]')


if __name__ == '__main__':
    main()