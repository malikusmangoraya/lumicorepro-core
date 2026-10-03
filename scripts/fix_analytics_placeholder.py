import pathlib, re, json

GEN = pathlib.Path('D:/lumicorepro-core/generated-projects')

OLD_RE = re.compile(
    r"(?P<i>[ \t]*)if \(window\.gtag\) \{\n"
    r"(?P=i)  window\.gtag\('event', 'conversion', \{ send_to: 'AW-xxx/yyy', value, currency \}\);\n"
    r"(?P=i)\}"
)

NEW = (
    "{i}if (window.gtag && ANALYTICS_CONFIG.primary.ga4MeasurementId) {{\n"
    "{i}  window.gtag('event', 'conversion', {{\n"
    "{i}    send_to: ANALYTICS_CONFIG.primary.ga4MeasurementId,\n"
    "{i}    value,\n"
    "{i}    currency,\n"
    "{i}  }});\n"
    "{i}}}"
)

IMPORT_ANCHOR = "import analytics from '@/config/analytics';"
IMPORT_NEW = (
    "import analytics from '@/config/analytics';\n"
    "import { ANALYTICS_CONFIG } from '@/config/analytics-config';"
)

report = []
for d in sorted(GEN.iterdir()):
    p = d / 'frontend' / 'src' / 'hooks' / 'useAnalytics.js'
    if not p.is_file():
        continue
    src = p.read_text(encoding='utf-8')
    if 'AW-xxx/yyy' not in src:
        continue
    m = OLD_RE.search(src)
    if not m:
        report.append({'slug': d.name, 'status': 'PATTERN-MISS'})
        continue
    i = m.group('i')
    src = src[:m.start()] + NEW.format(i=i) + src[m.end():]
    if 'analytics-config' not in src.split('\n\n')[0] and 'ANALYTICS_CONFIG' in src:
        if IMPORT_ANCHOR in src:
            src = src.replace(IMPORT_ANCHOR, IMPORT_NEW, 1)
        else:
            lines = src.split('\n')
            for idx, line in enumerate(lines):
                if line.startswith('import '):
                    lines.insert(idx + 1, "import { ANALYTICS_CONFIG } from '@/config/analytics-config';")
                    break
            src = '\n'.join(lines)
    p.write_text(src, encoding='utf-8', newline='\n')
    report.append({'slug': d.name, 'status': 'fixed'})

ok = sum(1 for r in report if r['status'] == 'fixed')
print(f'fixed: {ok}   problems: {len(report) - ok}')
for r in report:
    if r['status'] != 'fixed':
        print('  !', r['slug'], r['status'])
pathlib.Path('D:/lumicorepro-core/logs/rebuild/analytics-placeholder-fix.json').write_text(
    json.dumps(report, indent=2), encoding='utf-8')
