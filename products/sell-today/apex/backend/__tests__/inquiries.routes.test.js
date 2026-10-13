/**
 * Enquiry route integration coverage.
 *
 * Same spawned-server approach as `vehicles.routes.test.js`: the route modules
 * are ES modules, which this repo's CommonJS Jest setup cannot import directly.
 *
 * The important boundaries here are privacy ones, so the suite drives three
 * distinct identities (two buyers and an admin) and asserts that one buyer can
 * never observe another's enquiries.
 */
process.env.DATABASE_URL = '';

const { spawn } = require('child_process');
const path = require('path');
const jwt = require('jsonwebtoken');
const Vehicle = require('../models/Vehicle');
const Inquiry = require('../models/Inquiry');

const SECRET = 'ci-test-secret-32-chars-minimum-length-0123456789';
const PORT = 6600 + Math.floor(Math.random() * 300);
const BASE = `http://127.0.0.1:${PORT}`;

const BUYER_A = { id: 101, role: 'user', email: 'buyer.a@apex.test' };
const BUYER_B = { id: 202, role: 'user', email: 'buyer.b@apex.test' };
const ADMIN = { id: 1, role: 'admin', email: 'staff@apex.test' };

const ACTIVE_SLUG = 'enquiry-target-active';
const DRAFT_SLUG = 'enquiry-target-draft';

const token = (claims) => jwt.sign(claims, SECRET, { expiresIn: '15m', algorithm: 'HS256' });
const bearer = (claims) => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${token(claims)}`,
});
const jsonHeaders = { 'Content-Type': 'application/json' };

let proc;
let activeVehicleId;
let draftVehicleId;

async function fetchJson(pathname, opts = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(BASE + pathname, { ...opts, signal: controller.signal });
    const text = await res.text();
    try {
      return { status: res.status, body: JSON.parse(text) };
    } catch {
      return { status: res.status, body: text };
    }
  } finally {
    clearTimeout(timer);
  }
}

const enquiry = (overrides = {}) => ({
  name: 'Test Buyer',
  email: 'buyer.a@apex.test',
  phone: '+971500000000',
  message: 'Please send me the full service history for this vehicle.',
  consent_given: true,
  locale: 'en',
  ...overrides,
});

describe('inquiry routes (live server)', () => {
  beforeAll(async () => {
    await Vehicle.sync({ force: true });
    await Inquiry.sync({ force: true });
    await Inquiry.destroy({ where: {} });
    await Vehicle.destroy({ where: {} });

    const base = {
      make: 'Apex',
      model: 'GT',
      year: 2025,
      price: 148000,
      currency: 'USD',
      mileage: 1200,
      mileage_unit: 'km',
      location_country: 'AE',
      location_region: 'Dubai',
    };
    const active = await Vehicle.create({ ...base, slug: ACTIVE_SLUG, title: '2025 Apex GT', status: 'active' });
    const draft = await Vehicle.create({ ...base, slug: DRAFT_SLUG, title: '2025 Apex GT (draft)', status: 'draft' });
    activeVehicleId = active.id;
    draftVehicleId = draft.id;

    proc = spawn(process.execPath, ['server.js'], {
      cwd: path.join(__dirname, '..'),
      env: {
        ...process.env,
        NODE_ENV: 'test',
        PORT: String(PORT),
        JWT_SECRET: SECRET,
        DATABASE_URL: '',
        REDIS_DISABLED: 'true',
        CORS_ORIGIN: 'http://localhost:5173',
      },
      stdio: 'ignore',
    });

    let up = false;
    for (let i = 0; i < 60; i += 1) {
      try {
        await fetch(`${BASE}/health`);
        up = true;
        break;
      } catch {
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
    if (!up) throw new Error('server did not become ready');
  }, 90000);

  afterAll(() => {
    if (proc) proc.kill('SIGTERM');
  });

  describe('submission', () => {
    test('an anonymous visitor can submit with consent and it is stored without an owner', async () => {
      const res = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify(enquiry({ email: 'anon@apex.test', vehicleId: activeVehicleId })),
      });
      expect(res.status).toBe(201);
      expect(res.body.data.user_id).toBeNull();
      expect(res.body.data.vehicle_id).toBe(activeVehicleId);
      expect(res.body.data.status).toBe('new');
      expect(res.body.data.consent_given).toBe(true);
      expect(res.body.data.consent_at).toBeTruthy();
    });

    test('submission without consent is refused and nothing is stored', async () => {
      const before = await Inquiry.count();
      const res = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify(enquiry({ email: 'no-consent@apex.test', consent_given: false })),
      });
      expect(res.status).toBe(400);
      expect(res.body.errors[0].field).toBe('consent_given');
      expect(await Inquiry.count()).toBe(before);
    });

    test.each([
      ['a missing name', { name: undefined }],
      ['a one-character name', { name: 'A' }],
      ['a malformed email', { email: 'not-an-email' }],
      ['a missing email', { email: undefined }],
      ['a message below the minimum length', { message: 'too short' }],
      ['a missing message', { message: undefined }],
    ])('%s is refused with 400', async (_label, overrides) => {
      const res = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify(enquiry(overrides)),
      });
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    test('a draft vehicle cannot be enquired about', async () => {
      const res = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify(enquiry({ email: 'draft-probe@apex.test', vehicleId: draftVehicleId })),
      });
      expect(res.status).toBe(400);
    });

    test('an unknown vehicle id is refused', async () => {
      const res = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify(enquiry({ email: 'unknown-vehicle@apex.test', vehicleId: 987654 })),
      });
      expect(res.status).toBe(400);
    });

    test('an authenticated submission is bound to the session, not the payload', async () => {
      const res = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_A),
        body: JSON.stringify({
          ...enquiry({ email: BUYER_A.email, vehicleId: activeVehicleId }),
          user_id: BUYER_B.id,
          userId: BUYER_B.id,
        }),
      });
      expect(res.status).toBe(201);
      expect(res.body.data.user_id).toBe(BUYER_A.id);
    });

    test('replaying the same idempotency key does not create a second lead', async () => {
      const key = 'lead-idempotency-probe-1';
      const payload = enquiry({ email: BUYER_A.email, vehicleId: activeVehicleId, idempotency_key: key });

      const first = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_A),
        body: JSON.stringify(payload),
      });
      expect(first.status).toBe(201);

      const before = await Inquiry.count({ where: { idempotency_key: key } });
      expect(before).toBe(1);

      const replay = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_A),
        body: JSON.stringify(payload),
      });
      expect(replay.status).toBe(200);
      expect(replay.body.data.id).toBe(first.body.data.id);
      expect(await Inquiry.count({ where: { idempotency_key: key } })).toBe(1);
    });

    test('an idempotency key cannot be reused by a different sender', async () => {
      const key = 'lead-idempotency-probe-2';
      await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_A),
        body: JSON.stringify(enquiry({ email: BUYER_A.email, idempotency_key: key })),
      });
      const hijack = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_B),
        body: JSON.stringify(enquiry({ email: BUYER_B.email, idempotency_key: key })),
      });
      expect(hijack.status).toBe(400);
      expect(hijack.body.errors[0].field).toBe('idempotency_key');
    });
  });

  describe('ownership', () => {
    test('the buyer queue requires authentication', async () => {
      const res = await fetchJson('/api/inquiries/mine');
      expect(res.status).toBe(401);
    });

    test('a buyer sees only their own enquiries', async () => {
      await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_B),
        body: JSON.stringify({ ...enquiry({ email: BUYER_B.email }), message: 'Buyer B private enquiry message.' }),
      });

      const mine = await fetchJson('/api/inquiries/mine', { headers: bearer(BUYER_A) });
      expect(mine.status).toBe(200);
      expect(mine.body.data.items.length).toBeGreaterThan(0);
      expect(mine.body.data.items.every((i) => i.user_id === BUYER_A.id)).toBe(true);
      expect(mine.body.data.items.every((i) => i.email !== BUYER_B.email)).toBe(true);

      const other = await fetchJson('/api/inquiries/mine', { headers: bearer(BUYER_B) });
      expect(other.body.data.items.every((i) => i.user_id === BUYER_B.id)).toBe(true);
      const mineIds = new Set(mine.body.data.items.map((i) => i.id));
      expect(other.body.data.items.some((i) => mineIds.has(i.id))).toBe(false);
    });

    test('a userId in the query string cannot widen the scope (IDOR)', async () => {
      const mine = await fetchJson('/api/inquiries/mine', { headers: bearer(BUYER_A) });
      expect(mine.status).toBe(200);

      const probe = await fetchJson(`/api/inquiries/mine?userId=${BUYER_B.id}`, {
        headers: bearer(BUYER_A),
      });
      expect(probe.body.data.items.every((i) => i.user_id === BUYER_A.id)).toBe(true);
    });
  });

  describe('staff queue', () => {
    test('rejects anonymous and non-admin callers', async () => {
      expect((await fetchJson('/api/inquiries/admin')).status).toBe(401);
      expect((await fetchJson('/api/inquiries/admin', { headers: bearer(BUYER_A) })).status).toBe(403);
    });

    test('an admin sees every buyer enquiry with the vehicle summary', async () => {
      const res = await fetchJson('/api/inquiries/admin', { headers: bearer(ADMIN) });
      expect(res.status).toBe(200);
      expect(res.body.data.total).toBeGreaterThanOrEqual(2);
      const owned = res.body.data.items.filter((i) => i.user_id === BUYER_B.id);
      expect(owned.length).toBeGreaterThan(0);
      const withVehicle = res.body.data.items.find((i) => i.vehicle_id === activeVehicleId);
      expect(withVehicle.vehicle.slug).toBe(ACTIVE_SLUG);
    });

    test('an admin can filter the queue by status and it rejects unknown filters', async () => {
      const res = await fetchJson('/api/inquiries/admin?status=new&limit=5', { headers: bearer(ADMIN) });
      expect(res.status).toBe(200);
      expect(res.body.data.items.every((i) => i.status === 'new')).toBe(true);

      expect((await fetchJson('/api/inquiries/admin?status=nonsense', { headers: bearer(ADMIN) })).status).toBe(400);
      expect((await fetchJson('/api/inquiries/admin?bogus=1', { headers: bearer(ADMIN) })).status).toBe(400);
      expect((await fetchJson('/api/inquiries/admin?limit=101', { headers: bearer(ADMIN) })).status).toBe(400);
    });

    test('only an admin can advance a lead status', async () => {
      const created = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_A),
        body: JSON.stringify(enquiry({ email: BUYER_A.email, message: 'Status transition probe enquiry.' })),
      });
      const id = created.body.data.id;

      const buyer = await fetchJson(`/api/inquiries/${id}/status`, {
        method: 'PATCH',
        headers: bearer(BUYER_A),
        body: JSON.stringify({ status: 'contacted' }),
      });
      expect(buyer.status).toBe(403);

      const anon = await fetchJson(`/api/inquiries/${id}/status`, {
        method: 'PATCH',
        headers: jsonHeaders,
        body: JSON.stringify({ status: 'contacted' }),
      });
      expect(anon.status).toBe(401);

      const admin = await fetchJson(`/api/inquiries/${id}/status`, {
        method: 'PATCH',
        headers: bearer(ADMIN),
        body: JSON.stringify({ status: 'viewing_scheduled' }),
      });
      expect(admin.status).toBe(200);
      expect(admin.body.data.status).toBe('viewing_scheduled');

      const stored = await Inquiry.findByPk(id);
      expect(stored.status).toBe('viewing_scheduled');
    });

    test('an unknown status is refused and a missing enquiry is a 404', async () => {
      const created = await fetchJson('/api/inquiries', {
        method: 'POST',
        headers: bearer(BUYER_A),
        body: JSON.stringify(enquiry({ email: BUYER_A.email, message: 'Invalid status probe enquiry.' })),
      });

      const bad = await fetchJson(`/api/inquiries/${created.body.data.id}/status`, {
        method: 'PATCH',
        headers: bearer(ADMIN),
        body: JSON.stringify({ status: 'on-fire' }),
      });
      expect(bad.status).toBe(400);

      const missing = await fetchJson('/api/inquiries/987654/status', {
        method: 'PATCH',
        headers: bearer(ADMIN),
        body: JSON.stringify({ status: 'closed' }),
      });
      expect(missing.status).toBe(404);
    });
  });
});
