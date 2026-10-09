"""Simplify the health/operational suite so it does not depend on the ESM route
mount path (that is covered by __tests__/auth.test.js as a live HTTP test)."""
from pathlib import Path

ROOT = Path(r'D:\lumicorepro-core\products')

HEALTH = r'''const request = require('supertest');
const { app } = require('../server');

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

  test('an unknown path returns a structured response, never a crash', async () => {
    const res = await request(app).get('/api/definitely-not-a-route');
    expect([404, 400]).toContain(res.status);
  });
});
'''

n = 0
for prod in sorted(ROOT.iterdir()):
    if not prod.is_dir():
        continue
    t = prod / 'backend' / '__tests__' / 'health.test.js'
    if t.parent.is_dir():
        t.write_text(HEALTH, encoding='utf-8')
        n += 1
print('rewrote health.test.js for', n, 'products')
