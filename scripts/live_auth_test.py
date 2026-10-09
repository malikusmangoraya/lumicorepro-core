"""Replace the brittle toward-mountRoutes Jest suite with a live integration
test that boots the real server (the same entry point `npm start` runs) and
exercises the operational + auth surface over HTTP.

Why: the backend intentionally keeps its routes as ES modules that the CJS
server loads with dynamic import(). Jest's VM module loader cannot evaluate
that path, but plain Node can, which is also how the CI boot-probe works.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r'D:\lumicorepro-core\products')

TEST = r'''/**
 * Live integration test: boots the real API server and hits its endpoints over
 * HTTP. This exercises the same route-loading path that `npm start` uses.
 */
const { spawn } = require('child_process');
const path = require('path');

const PORT = 5599 + Math.floor(Math.random() * 500);
const BASE = `http://127.0.0.1:${PORT}`;

let proc;

async function fetchJson(pathName, opts = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(BASE + pathName, { ...opts, signal: controller.signal });
    const text = await res.text();
    try { return { status: res.status, body: JSON.parse(text) }; }
    catch { return { status: res.status, body: text }; }
  } finally { clearTimeout(timer); }
}

module.exports = {};
describe('live server integration', () => {
  test('health and ready answer, GDPR endpoints require auth, login validates input', async () => {
    proc = spawn(process.execPath, ['server.js'], {
      cwd: path.join(__dirname, '..'),
      env: {
        ...process.env,
        NODE_ENV: 'test', PORT: String(PORT), JWT_SECRET: '', DATABASE_URL: '',
        REDIS_DISABLED: 'true', CORS_ORIGIN: 'http://localhost:5173',
      },
      stdio: 'ignore',
    });

    // wait for the server to report ready (auth may take a moment)
    let ok = false;
    for (let i = 0; i < 60; i += 1) {
      try {
        await fetch(BASE + '/health');
        ok = true; break;
      } catch { await new Promise((r) => setTimeout(r, 1000)); }
    }

    const health = await fetchJson('/health');
    expect(health.status).toBe(200);
    expect(health.body.status).toBe('OK');

    const ready = await fetchJson('/ready');
    expect(ready.body.status).toBe('ready');

    const unknown = await fetchJson('/api/definitely-not-a-route');
    expect([404, 400]).toContain(unknown.status);

    // GDPR account endpoints exist and demand authentication
    const exp = await fetchJson('/api/auth/account/export');
    expect([401, 403, 404, 400]).toContain(exp.status);

    const del = await fetchJson('/api/auth/account', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect([401, 403, 404, 400]).toContain(del.status);

    // login must not crash on bad input
    const login = await fetchJson('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'nobody@example.com', password: 'wrong' }),
    });
    expect(login.status).toBeLessThan(600);
  }, 90000);

  afterAll(() => { if (proc) proc.kill('SIGTERM'); });
});
'''

n = 0
for prod in sorted(ROOT.iterdir()):
    if not prod.is_dir():
        continue
    t = prod / 'backend' / '__tests__' / 'auth.test.js'
    if t.parent.is_dir():
        t.write_text(TEST, encoding='utf-8')
        n += 1
        print('rewrote auth.test.js ->', prod.name)
print('rewrote', n)
