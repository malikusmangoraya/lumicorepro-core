/**
 * Vehicle schema + model coverage.
 *
 * Two layers are tested separately:
 *  1. migration 002 — its own DDL and rollback, run against a throwaway SQLite
 *     query interface so the test does not depend on a live PostgreSQL server.
 *  2. the Sequelize model — validation rules and the unique-slug constraint,
 *     run against the app's SQLite fallback (no DATABASE_URL in the test env).
 *
 * The 001 baseline migration is deliberately not exercised here: it creates the
 * legacy tables from `rawAttributes`, several of which use PostgreSQL-only
 * column types, so it cannot run on the SQLite test dialect at all.
 */
process.env.DATABASE_URL = '';

const { Sequelize } = require('sequelize');
const Vehicle = require('../models/Vehicle');
const createVehicles = require('../migrations/002-create-vehicles');

const EXPECTED_INDEXES = [
  'vehicles_status_idx',
  'vehicles_make_model_idx',
  'vehicles_year_idx',
  'vehicles_price_currency_idx',
  'vehicles_location_idx',
];

const validListing = (overrides = {}) => ({
  slug: '2024-porsche-911-carrera',
  make: 'Porsche',
  model: '911 Carrera',
  year: 2024,
  title: '2024 Porsche 911 Carrera',
  description: 'Single owner, full service history.',
  price: 148000,
  currency: 'USD',
  mileage: 12400,
  mileage_unit: 'km',
  location_country: 'AE',
  location_region: 'Dubai',
  status: 'active',
  ...overrides,
});

describe('migration 002 — vehicles table', () => {
  let sequelize;
  let queryInterface;

  beforeAll(() => {
    sequelize = new Sequelize({ dialect: 'sqlite', storage: ':memory:', logging: false });
    queryInterface = sequelize.getQueryInterface();
  });

  afterAll(async () => {
    await sequelize.close();
  });

  test('up creates the table with every declared index', async () => {
    await createVehicles.up({ context: queryInterface });

    expect(await queryInterface.tableExists('vehicles')).toBe(true);

    const described = await queryInterface.describeTable('vehicles');
    for (const column of ['slug', 'make', 'model', 'year', 'price', 'currency', 'status', 'created_at']) {
      expect(described).toHaveProperty(column);
    }

    const indexes = (await queryInterface.showIndex('vehicles')).map((i) => i.name);
    for (const name of EXPECTED_INDEXES) {
      expect(indexes).toContain(name);
    }
  });

  test('up is safe to run twice', async () => {
    await createVehicles.up({ context: queryInterface });
    expect(await queryInterface.tableExists('vehicles')).toBe(true);
  });

  test('down removes the table', async () => {
    await createVehicles.down({ context: queryInterface });
    expect(await queryInterface.tableExists('vehicles')).toBe(false);
  });

  test('the schema is not part of the 001 baseline', () => {
    expect(Vehicle.migrationManaged).toBe(true);
  });
});

describe('Vehicle model', () => {
  beforeAll(async () => {
    await Vehicle.sync({ force: true });
  });

  beforeEach(async () => {
    await Vehicle.destroy({ where: {} });
  });

  afterAll(async () => {
    await Vehicle.destroy({ where: {} });
  });

  test('a complete listing validates and round-trips', async () => {
    const created = await Vehicle.create(validListing());
    const found = await Vehicle.findByPk(created.id);

    expect(found.slug).toBe('2024-porsche-911-carrera');
    expect(found.currency).toBe('USD');
    expect(Number(found.price)).toBe(148000);
    expect(found.status).toBe('active');
  });

  test.each(['slug', 'make', 'model', 'year', 'title', 'price', 'currency', 'location_country'])(
    '%s is required',
    async (field) => {
      const incomplete = validListing({ [field]: null });
      await expect(Vehicle.build(incomplete).validate()).rejects.toThrow();
    }
  );

  test('a negative price is rejected', async () => {
    await expect(Vehicle.build(validListing({ price: -1 })).validate()).rejects.toThrow(
      /price cannot be negative/
    );
  });

  test('a negative mileage is rejected', async () => {
    await expect(Vehicle.build(validListing({ mileage: -5 })).validate()).rejects.toThrow(
      /mileage cannot be negative/
    );
  });

  test('a currency outside the supported list is rejected', async () => {
    await expect(Vehicle.build(validListing({ currency: 'XXX' })).validate()).rejects.toThrow(
      /not supported/
    );
  });

  test('a malformed currency is rejected', async () => {
    await expect(Vehicle.build(validListing({ currency: 'DOLLARS' })).validate()).rejects.toThrow();
  });

  test('currency is normalised to upper case', async () => {
    const vehicle = Vehicle.build(validListing({ currency: 'eur' }));
    expect(vehicle.currency).toBe('EUR');
  });

  test('an unknown status is rejected', async () => {
    await expect(Vehicle.build(validListing({ status: 'on-fire' })).validate()).rejects.toThrow();
  });

  test('an unknown mileage unit is rejected', async () => {
    await expect(Vehicle.build(validListing({ mileage_unit: 'miles' })).validate()).rejects.toThrow();
  });

  test('a malformed slug is rejected', async () => {
    await expect(Vehicle.build(validListing({ slug: 'Not A Slug!' })).validate()).rejects.toThrow(
      /hyphenated/
    );
  });

  test('slug is normalised to lower case', async () => {
    const vehicle = Vehicle.build(validListing({ slug: 'Apex-GT-2025' }));
    expect(vehicle.slug).toBe('apex-gt-2025');
  });

  test('a duplicate slug is refused by the database', async () => {
    await Vehicle.create(validListing());
    await expect(
      Vehicle.create(validListing({ title: 'A second listing with the same slug' }))
    ).rejects.toThrow(/unique|Validation/i);
  });

  test('an out-of-range model year is rejected', async () => {
    await expect(Vehicle.build(validListing({ year: 1780 })).validate()).rejects.toThrow();
  });

  test('the listing currency is kept separate from the price', async () => {
    const vehicle = await Vehicle.create(validListing({ price: 95000, currency: 'GBP' }));
    expect(vehicle.currency).toBe('GBP');
    expect(Number(vehicle.price)).toBe(95000);
  });
});
