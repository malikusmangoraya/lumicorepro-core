import pathlib, re, json

GEN = pathlib.Path('D:/lumicorepro-core/generated-projects')

REMAP = [
    ('/features',     ['/services', '/pricing', '/about']),
    ('/case-studies', ['/about', '/services', '/pricing']),
    ('/enterprise',   ['/contact', '/services', '/pricing']),
    ('/shop',         ['/services', '/pricing', '/about']),
    ('/blog',         ['/services', '/about', '/pricing']),
    ('/docs',         ['/services', '/about', '/contact']),
    ('/listings',     ['/services', '/properties', '/about']),
    ('/agents',       ['/about', '/services', '/contact']),
    ('/products',     ['/services', '/pricing', '/about']),
    ('/faq',          ['/services', '/about', '/contact']),
]

LABEL_RULES = [
    ('privacy',   ['/privacy', '/terms', '/about', '/contact']),
    ('terms',     ['/terms', '/privacy', '/about', '/contact']),
    ('legal',     ['/privacy', '/terms', '/about']),
    ('career',    ['/about', '/contact', '/services']),
    ('twitter',   ['/contact', '/about', '/']),
    ('linkedin',  ['/contact', '/about', '/']),
    ('github',    ['/contact', '/about', '/']),
    ('facebook',  ['/contact', '/about', '/']),
    ('instagram', ['/contact', '/about', '/']),
    ('support',   ['/contact', '/about', '/']),
    ('security',  ['/privacy', '/about', '/contact']),
    ('status',    ['/about', '/contact', '/']),
    ('about',     ['/about', '/contact', '/']),
    ('contact',   ['/contact', '/about', '/']),
]

A_RE = re.compile(r'<a\s+href="#"(?P<attrs>[^>]*)>(?P<body>.*?)</a>', re.S)


def routes_of(src):
    rs = set(re.findall(r'path=["\'](/[^"\']*)["\']', src))
    return {r for r in rs if r not in ('/', '*', '/*')}


def pick(cands, known):
    for c in cands:
        if c == '/' or c in known:
            return c
    return None


def label_route(label, known):
    low = label.lower()
    for key, cands in LABEL_RULES:
        if key in low:
            t = pick(cands, known)
            if t:
                return t
    return None


def fix_hash_anchors(src, known, changes):
    def repl(m):
        label = re.sub(r'<[^>]+>', ' ', m.group('body'))
        label = ' '.join(label.split())[:40]
        target = label_route(label, known)
        if not target:
            return m.group(0)
        attrs = m.group('attrs')
        changes.append(f'href="#" [{label}] -> {target}')
        return f'<Link to="{target}"{attrs}>{m.group("body")}</Link>'
    prev = None
    while prev != src:
        prev = src
        src = A_RE.sub(repl, src)
    return src


report = []
for d in sorted(GEN.iterdir()):
    fe = d / 'frontend'
    app = fe / 'src' / 'App.jsx'
    if not app.is_file():
        continue
    known = routes_of(app.read_text(encoding='utf-8', errors='replace'))
    changes = []

    for p in sorted((fe / 'src').rglob('*.jsx')):
        original = p.read_text(encoding='utf-8', errors='replace')
        src = original

        for dead, cands in REMAP:
            if f'"{dead}"' not in src:
                continue
            target = pick(cands, known)
            if not target:
                continue
            new = src.replace(f'to="{dead}"', f'to="{target}"')
            new = new.replace(f"to='{dead}'", f"to='{target}'")
            new = new.replace(f'href="{dead}"', f'href="{target}"')
            if new != src:
                changes.append(f'{dead} -> {target}')
                src = new

        src = fix_hash_anchors(src, known, changes)

        if src != original:
            if '<Link ' in src and 'react-router-dom' not in original:
                lines = src.split('\n')
                lines.insert(0, "import { Link } from 'react-router-dom';")
                src = '\n'.join(lines)
                changes.append('added react-router-dom import')
            p.write_text(src, encoding='utf-8', newline='\n')

    if changes:
        report.append({'slug': d.name, 'changes': changes})

tot = sum(len(r['changes']) for r in report)
print(f'projects touched: {len(report)}   replacements: {tot}')
for r in report[:8]:
    print(' ', r['slug'], r['changes'][:8])
pathlib.Path('D:/lumicorepro-core/logs/rebuild/dead-link-fixes.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
