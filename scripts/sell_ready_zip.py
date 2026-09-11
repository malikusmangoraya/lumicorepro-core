"""Package a generated project as a sell-ready ZIP distribution.

Creates `{project_name}-sell-ready.zip` beside the project (or in --out)
containing:

  - the full project source (node_modules/.git/dist/build/caches excluded)
  - LICENSE.md          — end-customer license (copied, or generated if missing)
  - LICENSE-SEAL.md     — generator origin seal (copied, or generated if missing)
  - README.md           — auto-generated marketing README (generate_readme.py)
  - screenshots/        — placeholder directory for marketing screenshots
  - demo-data/          — placeholder directory for sample content

Stdlib only (zipfile, os, pathlib, argparse, json, datetime).

Usage:
    python scripts/sell_ready_zip.py path/to/project
    python scripts/sell_ready_zip.py path/to/project --out dist
"""
import argparse
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_readme import generate_readme, load_spec

EXCLUDE_NAMES = {
    'node_modules', '.git', 'dist', 'build', 'out', 'coverage',
    '__pycache__', '.pytest_cache', '.ruff_cache', '.venv', 'venv',
}

# Manifests we write at the zip root; the project copies are redundant.
ZIP_ROOT_WRITES = {'LICENSE.md', 'LICENSE-SEAL.md', 'README.md'}

PLACEHOLDER = 'Drop files in this directory to include them in the sell-ready package.\n'


def _slugify(name):
    slug = ''.join(ch if ch.isalnum() else '-' for ch in str(name).strip().lower())
    return slug.strip('-') or 'project'


def _default_license(name):
    return (
        '# License — %s\n\n'
        '## Permitted Use\n'
        '- You may host, deploy, and commercially operate this project.\n'
        '- You may modify the source for your own projects.\n'
        '- Redistribution or resale of the source as-is requires a separate license.\n\n'
        '## Warranty\n'
        '- Provided "as-is", without warranty of any kind.\n'
        '- You are responsible for legal and service compliance of the final product.\n\n'
        '## AI Disclosure\n'
        '- This project was scaffolded with AI-assisted code generation. '
        'Review generated code before production use.\n'
    ) % name


def _default_seal(name):
    return (
        '# License Seal\n\n'
        '- Generator: **LumicorePro Core Generator**\n'
        '- Project: %s\n'
        '- Generated at: %s\n\n'
        'This seal confirms the project originated from the LumicorePro generator.\n'
    ) % (name, date.today().isoformat())


def _read_or_fallback(project_dir, filename, fallback):
    path = project_dir / filename
    if path.is_file():
        text = path.read_text(encoding='utf-8', errors='replace')
        if text.strip():
            return text
    return fallback


def _is_excluded(rel_parts):
    return any(part in EXCLUDE_NAMES for part in rel_parts)


def package(project_dir, out_dir=None):
    """Zip a generated project as a sell-ready bundle; returns the zip path."""
    project = Path(project_dir).resolve()
    if not project.is_dir():
        sys.exit('sell_ready_zip: not a directory: %s' % project)

    spec = {}
    try:
        spec = load_spec(project)
    except SystemExit:
        pass

    name = spec.get('project_name') or project.name or 'project'
    readme_md = generate_readme(spec) if spec else generate_readme({'project_name': name})
    license_md = _read_or_fallback(project, 'LICENSE.md', _default_license(name))
    seal_md = _read_or_fallback(project, 'LICENSE-SEAL.md', _default_seal(name))

    out = (Path(out_dir).resolve() if out_dir else project.parent)
    out.mkdir(parents=True, exist_ok=True)
    zip_path = out / ('%s-sell-ready.zip' % _slugify(name))

    count = 0
    with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname, content in (
            ('README.md', readme_md),
            ('LICENSE.md', license_md),
            ('LICENSE-SEAL.md', seal_md),
            ('screenshots/.gitkeep', PLACEHOLDER),
            ('demo-data/.gitkeep', PLACEHOLDER),
        ):
            zf.writestr(arcname, content)
            count += 1

        for file in sorted(project.rglob('*')):
            if not file.is_file():
                continue
            rel = file.relative_to(project).as_posix()
            if not rel or rel in ZIP_ROOT_WRITES:
                continue
            if _is_excluded(rel.split('/')):
                continue
            if file.resolve() == zip_path.resolve():
                continue
            zf.write(str(file), rel)
            count += 1

    print('sell_ready_zip: %d file(s) -> %s' % (count, zip_path))
    return zip_path


def main(argv=None):
    ap = argparse.ArgumentParser(description='Package a generated project as a sell-ready ZIP.')
    ap.add_argument('project_dir', help='path to the generated project directory')
    ap.add_argument('--out', default=None, help='output directory for the ZIP (default: beside the project)')
    args = ap.parse_args(argv)

    package(args.project_dir, args.out)


if __name__ == '__main__':
    main()