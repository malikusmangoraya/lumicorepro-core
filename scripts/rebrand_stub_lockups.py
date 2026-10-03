import pathlib, re, json, sys, hashlib
sys.path.insert(0, r'D:\lumicorepro-core\scripts')
import brand_map

GEN = pathlib.Path('D:/lumicorepro-core/generated-projects')

SHAPES = [
    'M32 12 L48 21 V39 L32 48 L16 39 V21 Z',
    'M14 44 L26 20 L38 44 Z',
    'M32 10 L52 32 L32 54 L12 32 Z',
    'M18 20 H46 V44 H18 Z',
    'M20 18 L44 32 L20 46 Z',
    'M16 24 A16 16 0 1 1 32 48 A16 16 0 1 1 16 24',
    'M14 32 L32 14 L50 32 L32 50 Z',
    'M22 14 V50 M42 14 V50 M22 32 H42',
]


def tokens(css):
    p = a = ''
    m = re.search(r'--t-primary:\s*(#[0-9a-fA-F]{3,8})', css)
    if m:
        p = m.group(1)
    m = re.search(r'--t-accent:\s*(#[0-9a-fA-F]{3,8})', css)
    if m:
        a = m.group(1)
    return p, a


TEMPLATE = '''import React from 'react';
import {{ Link }} from 'react-router-dom';

export default function BrandLockup({{ to = '/', size = 34, dark = false }}) {{
  const uid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const g1 = `br1-${{uid}}`;
  const g2 = `br2-${{uid}}`;
  const m1 = `url(#${{g1}})`;
  const m2 = `url(#${{g2}})`;
  return (
    <Link
      to={{to}}
      className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
      aria-label="{name}"
    >
      <svg viewBox="0 0 64 64" width={{size}} height={{size}} aria-hidden="true">
        <defs>
          <linearGradient id={{g1}} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="{primary}"/>
            <stop offset="1" stop-color="{secondary}"/>
          </linearGradient>
          <linearGradient id={{g2}} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="{secondary}"/>
            <stop offset="1" stop-color="{primary}"/>
          </linearGradient>
        </defs>
        <rect x="5" y="5" width="54" height="54" rx="15" fill={{m1}} opacity="0.14"/>
        <path d="{shape}" fill={{m1}}/>
        <path d="{shape}" fill="none" stroke={{m2}} strokeWidth="2.5" strokeLinejoin="round" opacity="0.85"/>
        <text x="32" y="39" text-anchor="middle" font-family="Inter, system-ui, sans-serif"
              font-size="20" font-weight="800" fill="#fff" letter-spacing="0.5">{monogram}</text>
      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={{dark ? 'text-white' : 'text-slate-900'}}>{first}</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
          {second}
        </span>
      </span>
    </Link>
  );
}}
'''

report = []
for slug, (name, industry, tagline) in brand_map.STUB_BRANDS.items():
    fe = GEN / slug / 'frontend'
    p = fe / 'src' / 'components' / 'LumicorePro.jsx'
    if not p.is_file():
        report.append({'slug': slug, 'status': 'no LumicorePro.jsx'})
        continue

    css = fe / 'src' / 'index.css'
    primary, accent = tokens(css.read_text(encoding='utf-8', errors='replace')) if css.is_file() else ('', '')
    primary = primary or '#7c3aed'
    accent = accent or primary

    shape = SHAPES[hashlib.md5(slug.encode()).digest()[0] % len(SHAPES)]
    monogram = ''.join(w[0] for w in name.split()[:2]).upper()
    parts = name.split(' ', 1)
    first = parts[0]
    second = ' ' + parts[1] if len(parts) > 1 else ''

    p.write_text(
        TEMPLATE.format(name=name, primary=primary, secondary=accent, shape=shape,
                        monogram=monogram, first=first, second=second.strip() or ''),
        encoding='utf-8', newline='\n')
    report.append({'slug': slug, 'status': 'rebranded', 'name': name, 'primary': primary})

ok = sum(1 for r in report if r['status'] == 'rebranded')
print(f'rebranded {ok}/{len(report)}')
for r in report:
    if r['status'] != 'rebranded':
        print('  !', r)
