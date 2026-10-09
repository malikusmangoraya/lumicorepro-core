"""Batch restyle + full-app deploy for all 14 live projects via ProDesign."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.pro_design import (
    restyle_project,
    build_and_deploy_ghpages,
    build_and_deploy_static,
    DIR_TO_REPO,
    UI_STYLE_DEFAULT,
)
from agent.gh_token import load_token as _load_gh_token

# Deterministic per-project style so the batch sweep shows off the whole wheel.
STYLE_ROTATION = [
    'glassmorphism', 'bento', 'neobrutalism', 'minimalist', 'neumorphism',
    'flat', 'claymorphism', 'skeuomorphism', 'dark',
]

ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED = ROOT / 'generated-projects'


def load_token() -> str:
    return _load_gh_token(env_files=[ROOT / '.env'])


def has_vite_frontend(project_dir: Path) -> bool:
    return (project_dir / 'frontend' / 'vite.config.js').exists() or (project_dir / 'frontend' / 'package.json').exists()


def main():
    token = load_token()
    if not token:
        print('ERROR: GITHUB_TOKEN missing in root .env')
        sys.exit(1)

    results = []
    for idx, (dirname, repo) in enumerate(DIR_TO_REPO.items()):
        project_dir = GENERATED / dirname
        if not project_dir.exists():
            print(f'SKIP {repo}: dir {dirname} not found')
            continue

        style = STYLE_ROTATION[idx % len(STYLE_ROTATION)]
        vite = has_vite_frontend(project_dir)
        print(f'\n=== {repo} ({dirname}) vite={vite} style={style} ===')

        if vite:
            ok = restyle_project(str(project_dir), repo, style)
            print(f'RESTYLE: {ok}')
            url = build_and_deploy_ghpages(str(project_dir), repo, token)
        else:
            url = build_and_deploy_static(repo, token)

        status = 'ok' if url else 'deploy-fail'
        results.append((repo, status, style, url))
        print(f'DEPLOY: {url or "FAIL"}')

    print('\n=== SUMMARY ===')
    for repo, status, style, url in results:
        print(f'{repo:<22} {status:<14} {style:<16} {url}')


if __name__ == '__main__':
    main()