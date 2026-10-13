/**
 * Vehicle route integration coverage.
 *
 * Boots the real API server in a child process and drives it over HTTP, which is
 * the only way to exercise these routes under this repo's Jest setup: the route
 * modules are ES modules and Jest loads test code as CommonJS, so a direct
 * `import()` of the router fails with "Cannot use import statement outside a
 * module". `auth.test.js` uses the same spawned-server pattern for the same
 * reason, and it additionally proves the routes actually mount.
 *
 * Admin/customer tokens are minted with the same secret the server verifies, so
 * this suite tests the real `protect`/`adminOnly` boundary without depending on
 * the login flow (which Phase 2/Task 5 reworks).
 */
process.env.DATABASE_URL = '';

const { spawn } = require('child_process');
const path = require('path');
const jwt = require('jsonwebtoken');
const Vehicle = require('../models/Vehicle');

const SECRET = 'ci-test-secret-32-chars-minimum-length-0123456789';
const PORT = 6100 + Math.floor(Math.random() * 400);
const BASE = `http://127.0.0.1:${PORT}`;

const ACTIVE_SLUG = 'apex-gt-active';
const DRAFT_SLUG = 'apex-gt-draft';

const token = (claims) => jwt.sign(claims, SECRET, { expiresIn: '15m', algorithm: 'HS256' });
const adminToken = () => token({ id: 1, role: 'admin' });
const buyerToken = () => token({ id: 2, role: 'user' });

let proc;

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

const json = (method, body, bearer) => ({
  method,
  headers: {
    'Content-Type': 'application/json',
    ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
  },
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});

const listing = (overrides = {}) => ({
  make: 'Apex',
  model: 'GT',
  year: 2025,
  title: '2025 Apex GT',
  description: 'Dealer-owned grand tourer.',
  price: 148000,
  currency: 'USD',
  mileage: 1200,
  mileage_unit: 'km',
  location_country: 'AE',
  location_region: 'Dubai',
  status: 'active',
  ...overrides,
});

describe('vehicle routes (live server)', () => {
  beforeAll(async () => {
    await Vehicle.sync({ force: true });
    await Vehicle.destroy({ where: {} });
    await Vehicle.bulkCreate([
      listing({ slug: ACTIVE_SLUG }),
      listing({ slug: DRAFT_SLUG, title: '2025 Apex GT (not published)', status: 'draft' }),
    ]);

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

  describe('public listing', () => {
    test('returns active listings and hides drafts', async () => {
      const res = await fetchJson('/api/vehicles');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);

      const slugs = res.body.data.items.map((v) => v.slug);
      expect(slugs).toContain(ACTIVE_SLUG);
      expect(slugs).not.toContain(DRAFT_SLUG);
      expect(res.body.data.total).toBe(1);
    });

    test('malformed, unknown and unbounded filters are refused with 400', async () => {
      const cases = [
        '?limit=61',
        '?limit=0',
        '?page=0',
        '?priceMin=200&priceMax=100',
        '?priceMin=-1',
        '?mileageMax=-1',
        '?yearMin=nineteen',
        '?sort=cheapest',
        '?currency=XXX',
        '?currency=DOLLARS',
        '?status=draft',
        '?bogus=1',
      ];

      for (const query of cases) {
        const res = await fetchJson(`/api/vehicles${query}`);
        expect({ query, status: res.status }).toEqual({ query, status: 400 });
        expect(res.body.success).toBe(false);
      }
    });

    test('a valid filter combination still succeeds', async () => {
      const res = await fetchJson(
        `/api/vehicles?make=Apex&currency=USD&priceMin=100000&priceMax=200000&sort=price_desc&limit=10&page=1`
      );
      expect(res.status).toBe(200);
      expect(res.body.data.items).toHaveLength(1);
    });

    test('detail returns an active listing', async () => {
      const res = await fetchJson(`/api/vehicles/${ACTIVE_SLUG}`);
      expect(res.status).toBe(200);
      expect(res.body.data.slug).toBe(ACTIVE_SLUG);
      expect(res.body.data.currency).toBe('USD');
    });

    test('detail does not disclose an inactive listing', async () => {
      const res = await fetchJson(`/api/vehicles/${DRAFT_SLUG}`);
      expect(res.status).toBe(404);
      expect(res.body.success).toBe(false);
    });

    test('detail returns 404 for an unknown slug', async () => {
      const res = await fetchJson('/api/vehicles/does-not-exist');
      expect(res.status).toBe(404);
    });
  });

  describe('admin boundary', () => {
    test('the admin listing rejects anonymous and non-admin callers', async () => {
      const anon = await fetchJson('/api/vehicles/admin');
      expect(anon.status).toBe(401);

      const buyer = await fetchJson('/api/vehicles/admin', json('GET', undefined, buyerToken()));
      expect(buyer.status).toBe(403);
    });

    test('an admin sees draft listings', async () => {
      const res = await fetchJson('/api/vehicles/admin', json('GET', undefined, adminToken()));
      expect(res.status).toBe(200);
      const slugs = res.body.data.items.map((v) => v.slug);
      expect(slugs).toContain(DRAFT_SLUG);
      expect(res.body.data.total).toBe(2);
    });

    test('writes reject anonymous and non-admin callers', async () => {
      const anon = await fetchJson('/api/vehicles', json('POST', listing({ slug: 'nope-anon' })));
      expect(anon.status).toBe(401);

      const buyer = await fetchJson(
        '/api/vehicles',
        json('POST', listing({ slug: 'nope-buyer' }), buyerToken())
      );
      expect(buyer.status).toBe(403);

      const remaining = await Vehicle.count({ where: { slug: ['nope-anon', 'nope-buyer'] } });
      expect(remaining).toBe(0);
    });

    test('an admin can create a listing and cannot mass-assign the id', async () => {
      const res = await fetchJson(
        '/api/vehicles',
        json('POST', { ...listing({ slug: undefined, title: '2025 Apex Roadster' }), id: 9999 }, adminToken())
      );
      expect(res.status).toBe(201);
      expect(res.body.data.id).not.toBe(9999);
      expect(res.body.data.slug).toBe('2025-apex-roadster');
      expect(res.body.data.status).toBe('active');

      const created = await Vehicle.findByPk(res.body.data.id);
      expect(created).not.toBeNull();
    });

    test('an admin cannot create a listing with an invalid status', async () => {
      const res = await fetchJson(
        '/api/vehicles',
        json('POST', listing({ slug: 'invalid-status-probe', status: 'on-fire' }), adminToken())
      );
      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
    });

    test('a duplicate slug is a conflict, not a silent overwrite', async () => {
      const res = await fetchJson(
        '/api/vehicles',
        json('POST', listing({ slug: ACTIVE_SLUG }), adminToken())
      );
      expect(res.status).toBe(409);
    });

    test('an admin can update a listing, a buyer cannot', async () => {
      const target = await Vehicle.findOne({ where: { slug: ACTIVE_SLUG } });

      const buyer = await fetchJson(
        `/api/vehicles/${target.id}`,
        json('PATCH', { price: 1 }, buyerToken())
      );
      expect(buyer.status).toBe(403);

      const admin = await fetchJson(
        `/api/vehicles/${target.id}`,
        json('PATCH', { price: 152000, id: 424242 }, adminToken())
      );
      expect(admin.status).toBe(200);
      expect(Number(admin.body.data.price)).toBe(152000);
      expect(admin.body.data.id).toBe(target.id);
    });

    test('updating a missing listing is a 404', async () => {
      const res = await fetchJson('/api/vehicles/987654', json('PATCH', { price: 1 }, adminToken()));
      expect(res.status).toBe(404);
    });

    test('DELETE withdraws the listing and it leaves the public showroom', async () => {
      const res = await fetchJson(
        '/api/vehicles',
        json('POST', listing({ slug: 'to-be-withdrawn' }), adminToken())
      );
      expect(res.status).toBe(201);
      const created = res.body.data;

      const withdrawn = await fetchJson(`/api/vehicles/${created.id}`, json('DELETE', undefined, adminToken()));
      expect(withdrawn.status).toBe(200);
      expect(withdrawn.body.data.status).toBe('withdrawn');

      const stillStored = await Vehicle.findByPk(created.id);
      expect(stillStored).not.toBeNull();

      const publicDetail = await fetchJson('/api/vehicles/to-be-withdrawn');
      expect(publicDetail.status).toBe(404);

      const publicList = await fetchJson('/api/vehicles');
      expect(publicList.body.data.items.map((v) => v.slug)).not.toContain('to-be-withdrawn');
    });

    test('withdrawing a missing listing is a 404', async () => {
      const res = await fetchJson('/api/vehicles/987654', json('DELETE', undefined, adminToken()));
      expect(res.status).toBe(404);
    });
  });
});
