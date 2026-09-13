"""Generate a marketing-ready README.md from a spec.json or a generated project dir.

Reads a project spec — a standalone spec.json, or the pipeline's
generation-report.json (which embeds user_prompt_spec + selected tech stack) —
and renders a README.md with the project name, description, feature list, tech
stack, quick-start setup and license sections. Stdlib only.

Usage:
    python scripts/generate_readme.py path/to/spec.json
    python scripts/generate_readme.py path/to/project            # auto-detect spec.json / generation-report.json
    python scripts/generate_readme.py path/to/project --out dist/README.md
"""
import argparse
import json
import sys
from pathlib import Path

LABEL_BY_ID = {
    'react': 'React 19',
    'vite': 'Vite',
    'tailwindcss': 'Tailwind CSS 3',
    'lucide-react': 'Lucide icons',
    'recharts': 'Recharts',
    'node': 'Node.js',
    'express': 'Express',
    'jwt+bcrypt': 'JWT + bcrypt auth',
    'postgresql': 'PostgreSQL',
    'mysql': 'MySQL',
    'mongodb': 'MongoDB',
    'sqlite': 'SQLite',
    'raw-sql': 'Raw SQL (parameterized)',
    'redis': 'Redis cache',
    'stripe': 'Stripe payments',
    'cloudflare': 'Cloudflare CDN',
}

DEFAULT_FEATURES = [
    'Responsive, mobile-first interface',
    'Dark mode and RTL support',
    'SEO and performance optimized',
    'Secure, validated backend API',
]

FALLBACK_TECH = [
    ('Frontend', 'React 19 + Vite + Tailwind CSS'),
    ('Backend', 'Node.js + Express'),
    ('Database', 'PostgreSQL'),
]


def _lower(value):
    return str(value or '').lower()


def _humanize(value):
    words = str(value).replace('_', ' ').replace('-', ' ').split()
    return ' '.join(w[:1].upper() + w[1:] for w in words) or str(value)


def _spec_from_report(report):
    """Extract a usable spec dict from a generation-report.json."""
    spec = dict(report.get('user_prompt_spec') or {})
    spec['project_name'] = (
        report.get('project_name') or spec.get('project_name') or 'generated-project'
    )
    if not spec.get('description') and spec.get('original_prompt'):
        spec['description'] = spec['original_prompt']
    resources = report.get('selected_resources') or {}
    if resources.get('tech_stack'):
        spec['tech_stack'] = resources['tech_stack']
    if not spec.get('features') and resources.get('components'):
        spec['features'] = [
            c.get('name') if isinstance(c, dict) else c
            for c in (resources.get('components') or [])
        ]
    return spec


def load_spec(source):
    """Load a spec dict from a spec.json, a report, or a project directory."""
    path = Path(source)
    if path.is_file():
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if 'user_prompt_spec' in data and 'generated_project_dir' in data:
            return _spec_from_report(data)
        return data
    if path.is_dir():
        for name in ('spec.json', 'generation-report.json'):
            candidate = path / name
            if candidate.is_file():
                data = json.loads(candidate.read_text(encoding='utf-8-sig'))
                return _spec_from_report(data) if name == 'generation-report.json' else data
        sys.exit('generate_readme: no spec.json or generation-report.json found in %s' % source)
    sys.exit('generate_readme: not a file or directory: %s' % source)


def _features(spec):
    raw = spec.get('features') or spec.get('trending_features') or []
    out, seen = [], set()
    for item in raw:
        value = ''
        if isinstance(item, dict):
            value = item.get('name') or item.get('title') or item.get('id') or ''
        elif item:
            value = str(item)
        key = _lower(value)
        if value and key not in seen:
            seen.add(key)
            out.append(_humanize(value))
    return out or list(DEFAULT_FEATURES)


def _label(value):
    if isinstance(value, dict):
        return _label(value.get('name') or value.get('id') or '')
    key = _lower(value)
    return LABEL_BY_ID.get(key, _humanize(value))


def _tech_rows(spec):
    stack = spec.get('tech_stack') or {}
    nested = bool(stack) and any(isinstance(stack.get(k), dict) for k in ('frontend', 'backend', 'database'))
    if stack and not nested:
        rows = [(_humanize(layer), _label(stack[layer])) for layer in ('frontend', 'backend', 'database') if stack.get(layer)]
        return rows
    rows = []
    for layer in ('frontend', 'backend', 'database'):
        value = stack.get(layer) if nested else spec.get(layer)
        if not value:
            continue
        if isinstance(value, dict):
            bits = []
            for key in ('framework', 'bundler', 'styling', 'engine', 'runtime', 'auth'):
                if value.get(key):
                    bits.append(_label(value[key]))
            label = ', '.join(dict.fromkeys(bits)) or _humanize(layer)
        else:
            label = _label(value)
        if label:
            rows.append((_humanize(layer), label))
    return rows or list(FALLBACK_TECH)


def generate_readme(spec, project_dir=None):
    """Render a marketplace-grade README: details, stack, and how to start."""
    agent_root = Path(__file__).resolve().parent.parent / 'ai-agent'
    if str(agent_root) not in sys.path:
        sys.path.insert(0, str(agent_root))
    from agent.marketplace_readme import generate_marketplace_readme

    mode = 'static'
    if project_dir:
        backend = Path(project_dir) / 'backend' / 'package.json'
        if backend.is_file():
            mode = 'fullstack'
    elif spec.get('backend') or (spec.get('tech_stack') or {}).get('backend'):
        mode = 'fullstack'
    return generate_marketplace_readme(spec, mode=mode)


def _default_out(source):
    path = Path(source)
    if path.is_dir():
        return path / 'README.md'
    return path.parent / 'README.md'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Generate a marketing-ready README.md from a project spec.')
    ap.add_argument('source', help='path to spec.json, generation-report.json, or a project directory')
    ap.add_argument('--out', default=None, help='output file path (default: README.md beside the source)')
    args = ap.parse_args(argv)

    spec = load_spec(args.source)
    out = Path(args.out) if args.out else _default_out(args.source)
    out.parent.mkdir(parents=True, exist_ok=True)
    source_path = Path(args.source)
    project_dir = str(source_path) if source_path.is_dir() else None
    out.write_text(generate_readme(spec, project_dir=project_dir), encoding='utf-8')
    print('README_OK %s' % out)


if __name__ == '__main__':
    main()