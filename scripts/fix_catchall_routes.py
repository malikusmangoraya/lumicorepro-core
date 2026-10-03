import pathlib, re, json, sys

GEN = pathlib.Path('D:/lumicorepro-core/generated-projects')
ROUTE_FOR = {
    'About': '/about', 'Services': '/services', 'Pricing': '/pricing',
    'Contact': '/contact', 'Login': '/login', 'Register': '/register',
    'Checkout': '/checkout', 'Admin': '/admin', 'Privacy': '/privacy',
    'Terms': '/terms',
}
ORDER = ['About', 'Services', 'Pricing', 'Contact', 'Login', 'Register',
         'Checkout', 'Admin', 'Privacy', 'Terms']

report = []
for d in sorted(GEN.iterdir()):
    fe = d / 'frontend'
    app = fe / 'src' / 'App.jsx'
    if not app.is_file():
        continue
    src = app.read_text(encoding='utf-8')
    routes = set(re.findall(r'path=["\'](/[^"\']*)["\']', src))
    if routes != {'/*'}:
        continue

    pages_dir = fe / 'src' / 'pages'
    pages = {p.stem for p in pages_dir.glob('*.jsx')} if pages_dir.is_dir() else set()
    present = [p for p in ORDER if p in pages]
    if not present:
        report.append((d.name, 'skipped: no routable pages', []))
        continue

    added = []

    # 1. lazy imports after the Home import
    imports = '\n'.join(
        f"const {p} = lazy(() => import(\"./pages/{p}\"));" for p in present
    )
    new_src, n = re.subn(
        r"(const Home = lazy\(\(\) => import\('\./pages/Home'\)\);\n)",
        r"\1" + imports.replace('\\', '\\\\') + "\n",
        src,
        count=1,
    )
    if n != 1:
        report.append((d.name, 'FAILED: Home import anchor not found', []))
        continue
    src = new_src
    added += [f'import:{p}' for p in present]

    # 2. route elements replacing the catch-all block
    block = '\n'.join(
        f'              <Route path="{ROUTE_FOR[p]}" element={{<{p} />}} />'
        for p in present
    )
    new_src, n = re.subn(
        r'[ \t]*<Route path="/\*"[ \t]*element=\{<Home />\}[ \t]*/>\n',
        block + '\n              <Route path="*" element={<Home />} />\n',
        src,
        count=1,
    )
    if n != 1:
        report.append((d.name, 'FAILED: catch-all route anchor not found', []))
        continue
    src = new_src
    added += [f'route:{ROUTE_FOR[p]}' for p in present]

    app.write_text(src, encoding='utf-8', newline='\n')
    report.append((d.name, 'fixed', added))

ok = sum(1 for _, s, _ in report if s == 'fixed')
for name, status, added in report:
    print(f"{name:<32} {status}  {len(added)//2} routes")
print(f'\nFIXED: {ok}/{len(report)}')
