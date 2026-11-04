const test = require('node:test');
const assert = require('node:assert');

// Safety: tests must never touch a production database. The suite only boots
// with a DB connection when TEST_DATABASE_URL is exported; otherwise it runs
// as a skipped/shell suite (node --test reports the skips, nothing mutates).
process.env.NODE_ENV = 'test';
const TEST_DATABASE_URL = process.env.TEST_DATABASE_URL;
const canUseDatabase = Boolean(TEST_DATABASE_URL);
if (TEST_DATABASE_URL) process.env.DATABASE_URL = TEST_DATABASE_URL;

const app = require('../server');

let server;
let baseUrl;

test.before(async () => {
  if (!canUseDatabase) return;
  await app.initDb();
  await new Promise((resolve) => {
    server = app.listen(0, () => {
      const port = server.address().port;
      baseUrl = `http://127.0.0.1:${port}`;
      resolve();
    });
  });
});

test.after(async () => {
  if (server) {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('GET /api/v1/health returns healthy', { skip: !canUseDatabase }, async () => {
  const res = await fetch(`${baseUrl}/api/v1/health`);
  assert.strictEqual(res.status, 200);
  const data = await res.json();
  assert.strictEqual(data.status, 'healthy');
});

test('Auth & Blog Generation end-to-end flow', { skip: !canUseDatabase }, async () => {
  const email = `test_${Date.now()}_${Math.random().toString(36).slice(2, 6)}@example.com`;

  // 1. Register
  const regRes = await fetch(`${baseUrl}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Automated Tester', email, password: 'StrongPassword123!' }),
  });
  assert.strictEqual(regRes.status, 201);
  const reg = await regRes.json();
  assert.strictEqual(reg.success, true);
  assert.ok(reg.token);
  assert.strictEqual(reg.user.email, email);

  // 2. Check Credits
  const credRes = await fetch(`${baseUrl}/api/v1/blog/credits`, {
    headers: { Authorization: `Bearer ${reg.token}` },
  });
  assert.strictEqual(credRes.status, 200);
  const cred = await credRes.json();
  assert.strictEqual(cred.success, true);
  assert.strictEqual(cred.data.balance, 50);

  // 3. Generate article (SSE stream)
  const genRes = await fetch(`${baseUrl}/api/v1/blog/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${reg.token}`,
      'X-Force-Demo': '1',
    },
    body: JSON.stringify({
      keyword: 'NextGen AI Applications',
      tone: 'professional',
      length: 'short',
    }),
  });
  assert.strictEqual(genRes.status, 200);
  const streamBody = await genRes.text();
  assert.ok(streamBody.includes('event: meta'));
  assert.ok(streamBody.includes('event: chunk'));
  assert.ok(streamBody.includes('event: done'));

  // 4. Verify History
  const histRes = await fetch(`${baseUrl}/api/v1/blog/history`, {
    headers: { Authorization: `Bearer ${reg.token}` },
  });
  assert.strictEqual(histRes.status, 200);
  const hist = await histRes.json();
  assert.strictEqual(hist.success, true);
  assert.strictEqual(hist.data.length, 1);
  assert.strictEqual(hist.data[0].keyword, 'NextGen AI Applications');

  // 5. Verify Credit deducted
  const credResAfter = await fetch(`${baseUrl}/api/v1/blog/credits`, {
    headers: { Authorization: `Bearer ${reg.token}` },
  });
  const credAfter = await credResAfter.json();
  assert.strictEqual(credAfter.data.balance, 49);
});
