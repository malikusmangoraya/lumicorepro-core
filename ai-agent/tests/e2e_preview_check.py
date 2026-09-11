"""E2E preview test — real generated project through FastAPI TestClient."""
import os
import re
import sys

AI_AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, AI_AGENT_DIR)

import server
from server import _runs
from fastapi.testclient import TestClient

project_dir = os.path.abspath(os.path.join(os.path.dirname(server.__file__), '..', 'generated-projects', 'food-restaurant-001'))
run_id = 'test-preview-e2e'
_runs[run_id] = {
    'status': 'done',
    'events': [],
    'result': {
        'project_name': 'food-restaurant-001',
        'generated_project_dir': project_dir,
        'quality_gates': {'overall_score': 92},
    },
}

client = TestClient(server.app)

r = client.post('/api/preview', json={'run_id': run_id})
print('CREATE STATUS:', r.status_code)
data = r.json()
slug = data['data']['slug'] if r.status_code == 200 else None
print('SLUG:', slug)
print('DIST EXISTS NOW:', os.path.isfile(os.path.join(project_dir, 'frontend', 'dist', 'index.html')))

if slug:
    r2 = client.get(f'/preview/{slug}')
    print('FETCH STATUS:', r2.status_code)
    print('CONTENT-TYPE:', r2.headers.get('content-type'))
    if r2.status_code == 200:
        has_root = 'id="root"' in r2.text
        has_title = '<title>food-restaurant-001</title>' in r2.text
        print('HAS #root:', has_root)
        print('HAS TITLE:', has_title)
        m = re.search(r'(?:src|href)="/?([^\s"\']+\.(?:js|css))"', r2.text)
        if m:
            asset_path = '/' + m.group(1).lstrip('/')
            r3 = client.get(f'/preview/{slug}{asset_path}')
            print('ASSET', asset_path, 'STATUS:', r3.status_code, 'TYPE:', r3.headers.get('content-type'))
        else:
            print('NO JS/CSS ASSET FOUND IN INDEX')
    else:
        print('BODY:', r2.text[:200])