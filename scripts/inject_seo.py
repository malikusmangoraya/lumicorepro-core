"""Inject per-project SEO into every generated frontend.

Policy (deliberate, documented):
- canonical origin = the project's own brand domain, derived deterministically
  from brand_map.BRANDS[slug]['name']. Never inherits the shared
  malikusmangoraya.github.io/build/ URL or example.com.
- og:image always points at a file that actually exists in public/.
- JSON-LD is Organization + WebSite with the real brand name and no
  fabricated ratings, addresses or review counts.
- sitemap.xml is generated from the real App.jsx route table.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import brand_map  # noqa: E402

GEN = pathlib.Path('D:/lumicorepro-core/generated-projects')
LOG = pathlib.Path('D:/lumicorepro-core/logs/rebuild/seo-injection.json')

# components that are not public pages: never advertise them in a sitemap
NON_PAGE = {'admin', 'login', 'register', 'checkout', 'error', 'notfound'}

ROUTE_FILES = {
    'home': 'Home', 'about': 'About', 'services': 'Services',
    'pricing': 'Pricing', 'contact': 'Contact', 'privacy': 'Privacy',
    'terms': 'Terms', 'checkout': 'Checkout', 'login': 'Login',
    'register': 'Register', 'admin': 'Admin', 'blog': 'Blog',
    'products': 'Products', 'tour3d': 'Tour3D', 'properties': 'Properties',
    'mortgagecalc': 'MortgageCalc', 'features': 'Features',
    'portfolio': 'Portfolio', 'team': 'Team', 'faq': 'Faq',
    'careers': 'Careers', 'news': 'News', 'gallery': 'Gallery',
    'menu': 'Menu', 'booking': 'Booking', 'tours': 'Tours',
    'solutions': 'Solutions', 'integrations': 'Integrations',
    'resources': 'Resources', 'partners': 'Partners', 'webinar': 'Webinar',
    'webinars': 'Webinars', 'event': 'Event', 'events': 'Events',
    'podcast': 'Podcast', 'membership': 'Membership', 'dashboard': 'Dashboard',
    'docs': 'Docs', 'help': 'Help', 'support': 'Support', 'careers-page': 'Careers',
    # dashed paths whose component name is not a simple capitalisation
    'tour-3d': 'Tour3D', 'calculator': 'MortgageCalc', 'mortgage-calc': 'MortgageCalc',
    'tour3d': 'Tour3D', 'loan-calculator': 'MortgageCalc', 'affordability': 'MortgageCalc',
}


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def card(slug):
    c = brand_map.BRANDS.get(slug) or {}
    name = c.get('name') or slug
    industry = c.get('industry') or 'saas'
    tagline = c.get('tagline') or ''
    return name, industry, tagline


def origin(slug, name):
    return f'https://{slugify(name)}.com'


def routes_from_app(app_path, pages_dir):
    """Return the real public route paths, in App.jsx order."""
    if not app_path.is_file():
        return []
    src = app_path.read_text(encoding='utf-8', errors='replace')
    found = []
    # path="/about"  (or path='/about')
    for m in re.finditer(r'path=["\'](/[^"\']*)["\']', src):
        p = m.group(1)
        if p not in found:
            found.append(p)
    # map element paths to their component, so we can filter non-pages
    element_for = {}
    for m in re.finditer(r'path=["\'](/[^"\']*)["\'][^>]*?element=\{<([A-Za-z0-9_]+)', src, re.S):
        element_for[m.group(1)] = m.group(2)
    routes = []
    for p in found:
        comp = element_for.get(p)
        if comp and comp.lower() in NON_PAGE:
            continue
        routes.append(p)
    if '/' not in routes:
        routes.insert(0, '/')
    return routes


def public_routes(routes, pages_dir):
    """Keep only routes whose page file actually exists on disk."""
    out = []
    for p in routes:
        if p == '/':
            out.append(p)
            continue
        key = p.strip('/').split('/')[0]
        want = ROUTE_FILES.get(key, key.capitalize())
        if (pages_dir / f'{want}.jsx').is_file() or (pages_dir / f'{want}.js').is_file():
            out.append(p)
    return out or ['/']


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


def build_head(slug, name, industry, tagline, orig, og_file, routes):
    title = f'{name} \u2014 {tagline}'.strip(' \u2014') if tagline else name
    if not (15 <= len(title) <= 70):
        title = f'{name} \u2014 {industry.replace("-", " ").title()} platform'
    desc = (f'{name} is a {industry.replace("-", " ")} platform built for teams that need '
            f'reliable results. {tagline}'.strip())
    if len(desc) > 158:
        desc = desc[:155].rsplit(' ', 1)[0] + '.'
    if len(desc) < 50:
        desc = f'{name} \u2014 {tagline} A {industry.replace("-", " ")} platform for modern teams.'
    og_url = f'{orig}/'
    og_img = f'{orig}/{og_file}'

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{og_url}#organization",
                "name": name,
                "url": og_url,
                "description": desc,
                "logo": {"@type": "ImageObject", "url": f"{orig}/logo.svg"},
            },
            {
                "@type": "WebSite",
                "@id": f"{og_url}#website",
                "url": og_url,
                "name": name,
                "description": desc,
                "inLanguage": "en",
                "publisher": {"@id": f"{og_url}#organization"},
            },
        ],
    }

    tags = f'''    <meta name="description" content="{esc(desc)}" />
    <meta name="theme-color" content="#0f172a" />
    <link rel="canonical" href="{esc(og_url)}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="{esc(name)}" />
    <meta property="og:title" content="{esc(title)}" />
    <meta property="og:description" content="{esc(desc)}" />
    <meta property="og:url" content="{esc(og_url)}" />
    <meta property="og:image" content="{esc(og_img)}" />
    <meta property="og:image:type" content="image/svg+xml" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:locale" content="en_US" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{esc(title)}" />
    <meta name="twitter:description" content="{esc(desc)}" />
    <meta name="twitter:image" content="{esc(og_img)}" />
    <script type="application/ld+json">
{json.dumps(jsonld, indent=2, ensure_ascii=False)}
    </script>
'''
    return title, desc, tags


def main():
    report = []
    for slug_dir in sorted(p for p in GEN.iterdir() if p.is_dir()):
        slug = slug_dir.name
        fe = slug_dir / 'frontend'
        idx = fe / 'index.html'
        if not idx.is_file():
            report.append({'slug': slug, 'status': 'no index.html'})
            continue

        name, industry, tagline = card(slug)
        orig = origin(slug, name)
        public = fe / 'public'
        public.mkdir(parents=True, exist_ok=True)

        # ---- og image: reuse an existing local asset, never point at a missing one
        og_file = ''
        for cand in ('og-image.svg', 'og.svg', 'og-image.png', 'og.jpg'):
            if (public / cand).is_file():
                og_file = cand
                break
        if not og_file:
            og_file = 'og-image.svg'
            (public / 'og-image.svg').write_text(og_svg(name, tagline, industry),
                                                 encoding='utf-8', newline='\n')

        # ---- favicon: the gate requires one
        if not any((public / f).is_file() for f in ('favicon.svg', 'favicon.ico', 'favicon.png')):
            (public / 'favicon.svg').write_text(fav_svg(name), encoding='utf-8', newline='\n')

        # ---- head rewrite
        src = idx.read_text(encoding='utf-8', errors='replace')
        title, desc, tags = build_head(slug, name, industry, tagline, orig, og_file, None)

        # strip every existing description/og/twitter/canonical/ld+json block
        src = re.sub(r'\n?[ \t]*<meta\s+name="description"[\s\S]*?/>', '', src, flags=re.I)
        src = re.sub(r'\n?[ \t]*<meta\s+property="og:[^"]*"[\s\S]*?/>', '', src, flags=re.I)
        src = re.sub(r'\n?[ \t]*<meta\s+name="twitter:[^"]*"[\s\S]*?/>', '', src, flags=re.I)
        src = re.sub(r'\n?[ \t]*<link[^>]*rel="canonical"[^>]*>', '', src, flags=re.I)
        src = re.sub(r'\n?[ \t]*<meta\s+name="theme-color"[\s\S]*?/>', '', src, flags=re.I)
        src = re.sub(r'\n?[ \t]*<script\s+type="application/ld\+json"[\s\S]*?</script>', '', src, flags=re.I)

        # title
        if re.search(r'<title>[\s\S]*?</title>', src, re.I):
            src = re.sub(r'<title>[\s\S]*?</title>', f'<title>{esc(title)}</title>', src,
                         count=1, flags=re.I)
        else:
            src = re.sub(r'(<head[^>]*>)', rf'\1\n    <title>{esc(title)}</title>', src, count=1)

        # favicon link if absent
        if not re.search(r'rel=["\']icon["\']', src, re.I):
            src = re.sub(r'(<head[^>]*>)', r'\1\n    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />',
                         src, count=1)

        # charset must stay inside the first 1024 bytes, so the SEO block goes
        # at the end of <head> rather than immediately after the opening tag
        src = re.sub(r'\s*</head>', '\n' + tags.rstrip() + '\n  </head>', src, count=1, flags=re.I)
        idx.write_text(src, encoding='utf-8', newline='\n')

        # ---- sitemap + robots from real routes
        routes = public_routes(
            routes_from_app(fe / 'src' / 'App.jsx', fe / 'src' / 'pages'), fe / 'src' / 'pages')
        today = '2026-09-30'
        urls = []
        for p in routes:
            loc = f'{orig}/' if p == '/' else f'{orig}{p}'
            urls.append(
                f'  <url>\n    <loc>{esc(loc)}</loc>\n'
                f'    <lastmod>{today}</lastmod>\n'
                f'    <changefreq>{"monthly" if p == "/" else "yearly"}</changefreq>\n'
                f'    <priority>{"1.0" if p == "/" else "0.6"}</priority>\n  </url>')
        sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                   + '\n'.join(urls) + '\n</urlset>\n')
        (public / 'sitemap.xml').write_text(sitemap, encoding='utf-8', newline='\n')
        (public / 'robots.txt').write_text(
            'User-agent: *\nAllow: /\n\n'
            f'Sitemap: {orig}/sitemap.xml\n', encoding='utf-8', newline='\n')

        report.append({'slug': slug, 'name': name, 'origin': orig, 'title': title,
                       'descLen': len(desc), 'ogFile': og_file, 'routes': routes})

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    ok = sum(1 for r in report if 'origin' in r)
    print(f'injected: {ok}/{len(report)}')
    bad = [r for r in report if 'origin' not in r]
    for r in bad:
        print('  !', r)
    rt = {}
    for r in report:
        if 'routes' in r:
            rt[len(r['routes'])] = rt.get(len(r['routes']), 0) + 1
    print('route-count distribution:', dict(sorted(rt.items())))


def og_svg(name, tagline, industry):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{esc(name)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f172a"/>
      <stop offset="1" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="80" y="80" width="1040" height="470" rx="24" fill="#ffffff" opacity="0.04"/>
  <text x="120" y="250" font-family="Inter, system-ui, sans-serif" font-size="72" font-weight="800" fill="#f8fafc">{esc(name)}</text>
  <text x="120" y="330" font-family="Inter, system-ui, sans-serif" font-size="34" fill="#cbd5e1">{esc(tagline)}</text>
  <text x="120" y="430" font-family="Inter, system-ui, sans-serif" font-size="24" letter-spacing="3" fill="#94a3b8">{esc(industry.replace('-', ' ').upper())}</text>
</svg>
'''


def fav_svg(name):
    initial = esc(name[:1].upper())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="{esc(name)}">
  <rect width="64" height="64" rx="14" fill="#0f172a"/>
  <text x="32" y="42" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="32" font-weight="800" fill="#f8fafc">{initial}</text>
</svg>
'''


if __name__ == '__main__':
    main()
