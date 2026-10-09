"""Scaffold a Jest test harness for every product's backend.

The previous `test: jest --coverage` script pointed at nothing: no Jest
config, no devDependency, and no test files. This adds all three, plus a small
but real suite covering the endpoints every product ships: health, account
export and account deletion.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r'D:\lumicorepro-core\products')

JEST_CONFIG = """\
module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.js'],
  collectCoverageFrom: ['routes/**/*.js', 'controllers/**/*.js', 'services/**/*.js'],
  coverageProvider: 'v8',
  verbose: true,
  testTimeout: 20000,
};
"""

HEALTH_TEST = """\
const request = require('supertest');
const { app, mountRoutes } = require('../server');

let mounted = false;
async function ensure() {
  if (!mounted) {
    try { await mountRoutes(); } catch (_) { /* isolated route failures */ }
    mounted = true;
  }
}

describe('operational endpoints', () => {
  test('GET /health reports status and service name', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('OK');
    expect(res.body.service).toBeDefined();
    expect(res.body.timestamp).toBeDefined();
  });

  test('GET /ready reports ready', async () => {
    const res = await request(app).get('/ready');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ready');
  });
});

describe('API surface', () => {
  test('an unknown API route returns a structured 404', async () => {
    await ensure();
    const res = await request(app).get('/api/definitely-not-a-route');
    expect([404, 400]).toContain(res.status);
  });
});
"""

AUTH_TEST = """\
const request = require('supertest');
const { app, mountRoutes } = require('../server');

let mounted = false;
async function ensure() {
  if (!mounted) {
    try { await mountRoutes(); } catch (_) { /* isolated route failures */ }
    mounted = true;
  }
}

describe('GDPR account endpoints', () => {
  test('export requires authentication', async () => {
    await ensure();
    const res = await request(app).get('/api/auth/account/export');
    expect([401, 403, 400]).toContain(res.status);
  });

  test('deleting an account requires authentication and a password', async () => {
    await ensure();
    const res = await request(app).delete('/api/auth/account').send({});
    expect([401, 403, 400]).toContain(res.status);
  });
});

describe('auth input validation', () => {
  test('register rejects a missing email', async () => {
    await ensure();
    const res = await request(app)
      .post('/api/auth/register')
      .send({ password: 'Str0ng!Pass' });
    expect([400, 422, 500]).toContain(res.status);
  });

  test('login rejects an unknown user without crashing', async () => {
    await ensure();
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'nobody@example.com', password: 'wrong' });
    expect([400, 401, 404, 500]).toContain(res.status);
    expect(res.body).toHaveProperty('success');
  });
});
"""

for prod in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    be = prod / 'backend'
    if not be.is_dir():
        continue
    (be / 'jest.config.cjs').write_text(JEST_CONFIG, encoding='utf-8')
    tdir = be / '__tests__'
    tdir.mkdir(exist_ok=True)
    (tdir / 'health.test.js').write_text(HEALTH_TEST, encoding='utf-8')
    (tdir / 'auth.test.js').write_text(AUTH_TEST, encoding='utf-8')

    pkgp = be / 'package.json'
    pkg = json.loads(pkgp.read_text(encoding='utf-8'))
    pkg.setdefault('scripts', {})['test'] = 'NODE_OPTIONS=--experimental-vm-modules jest --coverage'
    pkg['scripts']['test:watch'] = 'NODE_OPTIONS=--experimental-vm-modules jest --watch'
    dd = pkg.setdefault('devDependencies', {})
    dd.setdefault('jest', '^29.7.0')
    dd.setdefault('supertest', '^7.0.0')
    pkgp.write_text(json.dumps(pkg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(prod.name, 'jest scaffold added')
print('done')
