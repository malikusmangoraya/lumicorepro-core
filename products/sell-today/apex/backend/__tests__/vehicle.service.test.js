/**
 * Vehicle service coverage.
 *
 * The service is plain CommonJS on purpose: it is where the plan's review-focus
 * items live (malformed/unknown filters, inverted ranges, bounded pagination,
 * sort whitelist, public-vs-admin scoping, mass-assignment), so it must be
 * unit-testable under this repo's CommonJS-only Jest setup.
 */
process.env.DATABASE_URL = '';

const Vehicle = require('../models/Vehicle');
const svc = require('../services/vehicle.service');

const base = (overrides = {}) => ({
  make: 'Porsche',
  model: '911 Carrera',
  year: 2024,
  title: '2024 Porsche 911 Carrera',
  price: 148000,
  currency: 'USD',
  mileage: 12000,
  mileage_unit: 'km',
  location_country: 'AE',
  location_region: 'Dubai',
  body_style: 'Coupe',
  fuel_type: 'Petrol',
  transmission: 'Automatic',
  status: 'active',
  ...overrides,
});

describe('vehicle service', () => {
  beforeAll(async () => {
    await Vehicle.sync({ force: true });
  });

  beforeEach(async () => {
    await Vehicle.destroy({ where: {} });
    await Vehicle.bulkCreate([
      base({ slug: 'porsche-911' }),
      base({
        slug: 'bmw-m4', make: 'BMW', model: 'M4', year: 2022, title: '2022 BMW M4',
        price: 82000, currency: 'EUR', mileage: 30000, mileage_unit: 'mi',
        location_country: 'DE', location_region: 'Bavaria',
      }),
      base({
        slug: 'toyota-hilux', make: 'Toyota', model: 'Hilux', year: 2019, title: '2019 Toyota Hilux',
        price: 34000, currency: 'AED', mileage: 90000,
        location_country: 'AE', location_region: 'Sharjah',
        body_style: 'Pickup', fuel_type: 'Diesel', transmission: 'Manual',
      }),
      base({ slug: 'audi-rs6', make: 'Audi', model: 'RS6', title: '2024 Audi RS6', status: 'draft' }),
      base({ slug: 'merc-c63', make: 'Mercedes', model: 'C63', title: '2021 Mercedes C63', status: 'reserved' }),
      base({ slug: 'ford-mustang', make: 'Ford', model: 'Mustang', title: '2020 Ford Mustang', status: 'withdrawn' }),
    ]);
  });

  afterAll(async () => {
    await Vehicle.destroy({ where: {} });
  });

  describe('public listing scope', () => {
    test('returns active listings only', async () => {
      const result = await svc.listVehicles({});
      expect(result.total).toBe(3);
      expect(result.items.map((v) => v.slug).sort()).toEqual(['bmw-m4', 'porsche-911', 'toyota-hilux']);
      expect(result.items.every((v) => v.status === 'active')).toBe(true);
    });

    test('never exposes draft, reserved or withdrawn vehicles', async () => {
      for (const slug of ['audi-rs6', 'merc-c63', 'ford-mustang']) {
        const result = await svc.listVehicles({ q: slug });
        expect(result.total).toBe(0);
        await expect(svc.getPublicVehicleBySlug(slug)).rejects.toThrow(svc.VehicleNotFoundError);
      }
    });

    test('rejects the status filter on the public path', async () => {
      await expect(svc.listVehicles({ status: 'draft' })).rejects.toThrow(svc.VehicleValidationError);
    });

    test('returns a page envelope with pagination metadata', async () => {
      const result = await svc.listVehicles({ limit: '2', page: '1' });
      expect(result).toMatchObject({ page: 1, limit: 2, total: 3, hasMore: true });
      expect(result.items).toHaveLength(2);

      const lastPage = await svc.listVehicles({ limit: '2', page: '2' });
      expect(lastPage.items).toHaveLength(1);
      expect(lastPage.hasMore).toBe(false);
    });
  });

  describe('filtering', () => {
    test('filters by make', async () => {
      const result = await svc.listVehicles({ make: 'Porsche' });
      expect(result.items.map((v) => v.slug)).toEqual(['porsche-911']);
    });

    test('filters by currency', async () => {
      const result = await svc.listVehicles({ currency: 'eur' });
      expect(result.items.map((v) => v.slug)).toEqual(['bmw-m4']);
      expect(result.items[0].currency).toBe('EUR');
    });

    test('filters by price range', async () => {
      const result = await svc.listVehicles({ priceMin: '50000', priceMax: '100000' });
      expect(result.items.map((v) => v.slug)).toEqual(['bmw-m4']);
    });

    test('filters by year range', async () => {
      const result = await svc.listVehicles({ yearMin: '2020' });
      expect(result.items.map((v) => v.slug).sort()).toEqual(['bmw-m4', 'porsche-911']);
    });

    test('filters by country and region text', async () => {
      const byCountry = await svc.listVehicles({ country: 'ae' });
      expect(byCountry.items.map((v) => v.slug).sort()).toEqual(['porsche-911', 'toyota-hilux']);

      const byRegion = await svc.listVehicles({ q: 'Sharjah' });
      expect(byRegion.items.map((v) => v.slug)).toEqual(['toyota-hilux']);
    });

    test('filters by mileage ceiling and unit', async () => {
      const byMax = await svc.listVehicles({ mileageMax: '40000' });
      expect(byMax.items.map((v) => v.slug).sort()).toEqual(['bmw-m4', 'porsche-911']);

      const byUnit = await svc.listVehicles({ mileageUnit: 'mi' });
      expect(byUnit.items.map((v) => v.slug)).toEqual(['bmw-m4']);
    });

    test('filters by body style', async () => {
      const result = await svc.listVehicles({ bodyStyle: 'Pickup' });
      expect(result.items.map((v) => v.slug)).toEqual(['toyota-hilux']);
    });

    test('free-text search matches make, model and title', async () => {
      expect((await svc.listVehicles({ q: 'Hilux' })).items.map((v) => v.slug)).toEqual(['toyota-hilux']);
      expect((await svc.listVehicles({ q: 'Carrera' })).items.map((v) => v.slug)).toEqual(['porsche-911']);
      expect((await svc.listVehicles({ q: 'Toyota' })).items.map((v) => v.slug)).toEqual(['toyota-hilux']);
    });

    test('combines filters with AND semantics', async () => {
      const result = await svc.listVehicles({ country: 'AE', priceMax: '50000' });
      expect(result.items.map((v) => v.slug)).toEqual(['toyota-hilux']);
    });

    test('a query that matches nothing returns an empty page', async () => {
      const result = await svc.listVehicles({ make: 'Ferrari' });
      expect(result).toMatchObject({ total: 0, hasMore: false });
      expect(result.items).toEqual([]);
    });
  });

  describe('sorting', () => {
    test('sorts by price ascending and descending', async () => {
      expect((await svc.listVehicles({ sort: 'price_asc' })).items[0].slug).toBe('toyota-hilux');
      expect((await svc.listVehicles({ sort: 'price_desc' })).items[0].slug).toBe('porsche-911');
    });

    test('sorts by year and mileage', async () => {
      expect((await svc.listVehicles({ sort: 'year_asc' })).items[0].slug).toBe('toyota-hilux');
      expect((await svc.listVehicles({ sort: 'mileage_asc' })).items[0].slug).toBe('porsche-911');
      expect((await svc.listVehicles({ sort: 'mileage_desc' })).items[0].slug).toBe('toyota-hilux');
    });

    test('rejects a sort key outside the whitelist', async () => {
      await expect(svc.listVehicles({ sort: 'cheapest' })).rejects.toThrow(svc.VehicleValidationError);
      await expect(svc.listVehicles({ sort: 'price; DROP TABLE vehicles' })).rejects.toThrow(
        svc.VehicleValidationError
      );
    });
  });

  describe('malformed and hostile filters', () => {
    test.each([
      ['an unknown filter key', { bogus: '1' }],
      ['a repeated (array) filter value', { make: ['Porsche', 'BMW'] }],
      ['a non-numeric year', { yearMin: 'nineteen' }],
      ['a non-numeric price', { priceMin: 'cheap' }],
      ['an infinite price bound', { priceMax: 'Infinity' }],
      ['an empty free-text query', { q: '   ' }],
      ['an over-long free-text query', { q: 'x'.repeat(81) }],
      ['a fractional page', { page: '1.5' }],
      ['a zero page', { page: '0' }],
      ['a negative page', { page: '-1' }],
      ['a page beyond the cap', { page: '10001' }],
      ['a zero limit', { limit: '0' }],
      ['a limit above the cap', { limit: '61' }],
      ['a negative limit', { limit: '-5' }],
      ['a negative price bound', { priceMin: '-1' }],
      ['inverted price bounds', { priceMin: '200', priceMax: '100' }],
      ['inverted year bounds', { yearMin: '2025', yearMax: '2000' }],
      ['a negative mileage ceiling', { mileageMax: '-1' }],
      ['a malformed currency', { currency: 'DOLLARS' }],
      ['an unsupported currency', { currency: 'XXX' }],
      ['a malformed country', { country: 'United Arab Emirates' }],
      ['an unknown mileage unit', { mileageUnit: 'miles' }],
      ['an unknown status', { status: 'on-fire' }],
    ])('%s is rejected with a validation error', async (_label, query) => {
      await expect(svc.listVehicles(query)).rejects.toThrow(svc.VehicleValidationError);
    });

    test('the validation error reports the offending field', async () => {
      try {
        await svc.listVehicles({ priceMin: '-1' });
        throw new Error('expected a validation error');
      } catch (err) {
        expect(err.status).toBe(400);
        expect(err.errors[0]).toMatchObject({ field: 'priceMin' });
      }
    });

    test('a non-object query is rejected', async () => {
      await expect(svc.listVehicles(['make=Porsche'])).rejects.toThrow(svc.VehicleValidationError);
    });

    test('LIKE wildcards in free text are escaped rather than treated as filters', () => {
      expect(svc.escapeLike('100%')).toBe('100\\%');
      expect(svc.escapeLike('a_b')).toBe('a\\_b');
    });
  });

  describe('admin listing scope', () => {
    test('admin mode returns every status', async () => {
      const result = await svc.listVehicles({}, { includeInactive: true });
      expect(result.total).toBe(6);
    });

    test('admin mode honours an explicit status filter', async () => {
      const result = await svc.listVehicles({ status: 'draft' }, { includeInactive: true });
      expect(result.items.map((v) => v.slug)).toEqual(['audi-rs6']);
    });

    test('admin mode still rejects an unknown status', async () => {
      await expect(
        svc.listVehicles({ status: 'on-fire' }, { includeInactive: true })
      ).rejects.toThrow(svc.VehicleValidationError);
    });
  });

  describe('detail lookup', () => {
    test('an active slug resolves', async () => {
      const vehicle = await svc.getPublicVehicleBySlug('porsche-911');
      expect(vehicle.make).toBe('Porsche');
    });

    test('slug normalisation is case-insensitive', async () => {
      const vehicle = await svc.getPublicVehicleBySlug('Porsche-911');
      expect(vehicle.slug).toBe('porsche-911');
    });

    test('an inactive slug is not found', async () => {
      await expect(svc.getPublicVehicleBySlug('audi-rs6')).rejects.toThrow(svc.VehicleNotFoundError);
    });

    test('an unusable slug is a validation error, not a 500', async () => {
      await expect(svc.getPublicVehicleBySlug('')).rejects.toThrow(svc.VehicleValidationError);
      await expect(svc.getPublicVehicleBySlug(undefined)).rejects.toThrow(svc.VehicleValidationError);
    });
  });

  describe('admin writes', () => {
    test('creates a listing and generates a slug when none is supplied', async () => {
      const created = await svc.createVehicle({
        make: 'Lexus', model: 'LC500', year: 2025, title: '2025 Lexus LC500',
        price: 97000, currency: 'USD', mileage: 4000, mileageUnit: 'km',
        locationCountry: 'AE', locationRegion: 'Abu Dhabi', status: 'active',
      });
      expect(created.slug).toBe('2025-lexus-lc500');
      expect(created.mileage_unit).toBe('km');
      expect(created.location_country).toBe('AE');

      const listed = await svc.listVehicles({ make: 'Lexus' });
      expect(listed.total).toBe(1);
    });

    test('ignores an attempt to set the id or a timestamp', async () => {
      const created = await svc.createVehicle({
        id: 9999,
        created_at: '2000-01-01T00:00:00.000Z',
        updated_at: '2000-01-01T00:00:00.000Z',
        slug: 'mass-assignment-probe',
        make: 'Lexus', model: 'LC500', year: 2025, title: '2025 Lexus LC500',
        price: 97000, currency: 'USD', location_country: 'AE',
      });
      expect(created.id).not.toBe(9999);
      expect(new Date(created.created_at).getFullYear()).toBeGreaterThan(2020);
    });

    test('ignores unknown fields rather than persisting them', async () => {
      const created = await svc.createVehicle(base({ slug: 'unknown-fields', role: 'admin', is_admin: true }));
      expect(created.role).toBeUndefined();
      expect(created.is_admin).toBeUndefined();
    });

    test('refuses an explicit duplicate slug with a conflict', async () => {
      await expect(svc.createVehicle(base({ slug: 'porsche-911' }))).rejects.toThrow(
        svc.VehicleConflictError
      );
    });

    test('refuses an unknown status', async () => {
      await expect(
        svc.createVehicle(base({ slug: 'bad-status', status: 'on-fire' }))
      ).rejects.toThrow(svc.VehicleValidationError);
    });

    test('refuses a listing with no price', async () => {
      await expect(svc.createVehicle(base({ slug: 'no-price', price: null }))).rejects.toThrow(
        svc.VehicleValidationError
      );
    });

    test('updates the fields an admin is allowed to change', async () => {
      const target = await Vehicle.findOne({ where: { slug: 'porsche-911' } });
      const updated = await svc.updateVehicle(target.id, { price: 152000, currency: 'GBP' });
      expect(Number(updated.price)).toBe(152000);
      expect(updated.currency).toBe('GBP');
    });

    test('an update cannot change the id', async () => {
      const target = await Vehicle.findOne({ where: { slug: 'porsche-911' } });
      const updated = await svc.updateVehicle(target.id, { id: 424242, price: 100000 });
      expect(updated.id).toBe(target.id);
    });

    test('updating a missing listing is a 404', async () => {
      await expect(svc.updateVehicle(987654, { price: 1 })).rejects.toThrow(svc.VehicleNotFoundError);
    });

    test('withdrawing flips the status without deleting the row', async () => {
      const target = await Vehicle.findOne({ where: { slug: 'bmw-m4' } });
      const withdrawn = await svc.withdrawVehicle(target.id);
      expect(withdrawn.status).toBe('withdrawn');

      const stillThere = await Vehicle.findByPk(target.id);
      expect(stillThere).not.toBeNull();
      expect((await svc.listVehicles({})).total).toBe(2);
    });

    test('withdrawing an already withdrawn listing is idempotent', async () => {
      const target = await Vehicle.findOne({ where: { slug: 'ford-mustang' } });
      const again = await svc.withdrawVehicle(target.id);
      expect(again.status).toBe('withdrawn');
    });

    test('withdrawing a missing listing is a 404', async () => {
      await expect(svc.withdrawVehicle(987654)).rejects.toThrow(svc.VehicleNotFoundError);
    });
  });

  describe('slug generation', () => {
    test('strips accents, punctuation and case', () => {
      expect(svc.slugify('2024 Citroën C4 — Édition!')).toBe('2024-citroen-c4-edition');
    });

    test('falls back to a stable placeholder for unusable input', () => {
      expect(svc.slugify('###')).toBe('vehicle');
      expect(svc.slugify('')).toBe('vehicle');
    });

    test('disambiguates a generated slug that is already taken', async () => {
      const created = await svc.createVehicle(base({ slug: undefined, title: '2024 Porsche 911 Carrera' }));
      expect(created.slug).toBe('2024-porsche-911-carrera');
      const second = await svc.createVehicle(base({ slug: undefined, title: '2024 Porsche 911 Carrera' }));
      expect(second.slug).toBe('2024-porsche-911-carrera-2');
    });
  });
});
