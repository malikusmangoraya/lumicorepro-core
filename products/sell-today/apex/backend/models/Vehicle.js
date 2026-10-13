/**
 * Vehicle — one unit of Apex-owned dealership inventory.
 *
 * Deliberately narrow: a listing describes a physical car Apex owns, the
 * authoritative price/currency for it, and the facts a buyer needs to decide
 * whether to enquire. Money and mileage are stored as numbers; `currency` is
 * the listing currency (never a converted value).
 *
 * `migrationManaged = true` tells the baseline migration (001) to leave this
 * table alone, so the table is created — with its indexes and constraints — by
 * the versioned migration 002 instead. Without the flag a fresh install would
 * create `vehicles` from `rawAttributes` first and migration 002 would then
 * collide with it.
 */
const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const STATUSES = ['draft', 'active', 'reserved', 'sold', 'withdrawn'];
const MILEAGE_UNITS = ['km', 'mi'];

/**
 * ISO 4217 codes Apex is willing to price inventory in. Filtering by any other
 * code is rejected rather than silently returning an empty result set.
 */
const SUPPORTED_CURRENCIES = [
  'AED', 'ARS', 'AUD', 'BHD', 'BRL', 'CAD', 'CHF', 'CLP', 'CNY', 'COP',
  'CZK', 'DKK', 'EGP', 'EUR', 'GBP', 'HKD', 'HUF', 'IDR', 'ILS', 'INR',
  'ISK', 'JOD', 'JPY', 'KES', 'KRW', 'KWD', 'MAD', 'MXN', 'MYR', 'NGN',
  'NOK', 'NZD', 'OMR', 'PEN', 'PHP', 'PKR', 'PLN', 'QAR', 'RON', 'RUB',
  'SAR', 'SEK', 'SGD', 'THB', 'TRY', 'TWD', 'UAH', 'USD', 'ZAR',
];

/** Sort keys the public API accepts, mapped to safe ORDER BY clauses. */
const SORT_OPTIONS = {
  newest: [['created_at', 'DESC']],
  price_asc: [['price', 'ASC']],
  price_desc: [['price', 'DESC']],
  year_desc: [['year', 'DESC']],
  year_asc: [['year', 'ASC']],
  mileage_asc: [['mileage', 'ASC']],
  mileage_desc: [['mileage', 'DESC']],
};

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const CURRENCY_PATTERN = /^[A-Z]{3}$/;
const COUNTRY_PATTERN = /^[A-Z]{2}$/;
const VIN_PATTERN = /^[A-HJ-NPR-Z0-9]{17}$/;

const LATEST_MODEL_YEAR = () => new Date().getUTCFullYear() + 2;
const EARLIEST_MODEL_YEAR = 1900;

const Vehicle = sequelize.define(
  'Vehicle',
  {
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    slug: {
      type: DataTypes.STRING(160),
      allowNull: false,
      unique: true,
      validate: {
        notEmpty: { msg: 'slug is required' },
        is: { args: SLUG_PATTERN, msg: 'slug must be a lower-case hyphenated string' },
      },
      set(value) {
        this.setDataValue('slug', String(value || '').trim().toLowerCase());
      },
    },
    make: {
      type: DataTypes.STRING(80),
      allowNull: false,
      validate: { notEmpty: { msg: 'make is required' } },
    },
    model: {
      type: DataTypes.STRING(120),
      allowNull: false,
      validate: { notEmpty: { msg: 'model is required' } },
    },
    year: {
      type: DataTypes.INTEGER,
      allowNull: false,
      validate: {
        isInt: { msg: 'year must be an integer' },
        isWithinModelYears(value) {
          if (value < EARLIEST_MODEL_YEAR || value > LATEST_MODEL_YEAR()) {
            throw new Error(`year must be between ${EARLIEST_MODEL_YEAR} and ${LATEST_MODEL_YEAR()}`);
          }
        },
      },
    },
    title: {
      type: DataTypes.STRING(200),
      allowNull: false,
      validate: { notEmpty: { msg: 'title is required' } },
    },
    description: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    price: {
      type: DataTypes.DECIMAL(14, 2),
      allowNull: false,
      validate: {
        isDecimal: { msg: 'price must be a decimal amount' },
        min: { args: [0], msg: 'price cannot be negative' },
      },
    },
    currency: {
      type: DataTypes.STRING(3),
      allowNull: false,
      validate: {
        isSupported(value) {
          const code = String(value || '').toUpperCase();
          if (!CURRENCY_PATTERN.test(code)) {
            throw new Error('currency must be a three-letter ISO 4217 code');
          }
          if (!SUPPORTED_CURRENCIES.includes(code)) {
            throw new Error(`currency ${code} is not supported for listings`);
          }
        },
      },
      set(value) {
        this.setDataValue('currency', String(value || '').trim().toUpperCase());
      },
    },
    mileage: {
      type: DataTypes.INTEGER,
      allowNull: false,
      defaultValue: 0,
      validate: {
        isInt: { msg: 'mileage must be a whole number' },
        min: { args: [0], msg: 'mileage cannot be negative' },
      },
    },
    mileage_unit: {
      type: DataTypes.STRING(2),
      allowNull: false,
      defaultValue: 'km',
      validate: { isIn: { args: [MILEAGE_UNITS], msg: 'mileage_unit must be km or mi' } },
    },
    body_style: { type: DataTypes.STRING(40), allowNull: true },
    fuel_type: { type: DataTypes.STRING(40), allowNull: true },
    transmission: { type: DataTypes.STRING(40), allowNull: true },
    location_country: {
      type: DataTypes.STRING(2),
      allowNull: false,
      validate: { is: { args: COUNTRY_PATTERN, msg: 'location_country must be an ISO 3166-1 alpha-2 code' } },
      set(value) {
        this.setDataValue('location_country', String(value || '').trim().toUpperCase());
      },
    },
    location_region: { type: DataTypes.STRING(120), allowNull: true },
    status: {
      type: DataTypes.STRING(20),
      allowNull: false,
      defaultValue: 'draft',
      validate: { isIn: { args: [STATUSES], msg: 'status is not a known listing state' } },
    },
    /** Ordered gallery: [{ url, alt, width, height, caption }]. */
    media: { type: DataTypes.JSON, allowNull: true },
    /** Ordered references to inspection documents Apex holds for this unit. */
    inspection_references: { type: DataTypes.JSON, allowNull: true },
    provenance_verified: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false },
    condition_notes: { type: DataTypes.TEXT, allowNull: true },
    condition_report_url: { type: DataTypes.STRING(500), allowNull: true },
    vin: {
      type: DataTypes.STRING(17),
      allowNull: true,
      validate: {
        isVin(value) {
          if (value === null || value === undefined || value === '') return;
          if (!VIN_PATTERN.test(String(value).toUpperCase())) {
            throw new Error('vin must be 17 characters and must not contain I, O or Q');
          }
        },
      },
      set(value) {
        const trimmed = String(value || '').trim();
        this.setDataValue('vin', trimmed ? trimmed.toUpperCase() : null);
      },
    },
  },
  {
    tableName: 'vehicles',
    timestamps: true,
    underscored: true,
    createdAt: 'created_at',
    updatedAt: 'updated_at',
    validate: {
      /** A public listing must carry enough to be shown honestly. */
      publicListingIsComplete() {
        if (this.status !== 'active') return;
        if (!this.location_country) throw new Error('an active listing needs a location_country');
        if (!this.title) throw new Error('an active listing needs a title');
      },
    },
    indexes: [
      { name: 'vehicles_status_idx', fields: ['status'] },
      { name: 'vehicles_make_model_idx', fields: ['make', 'model'] },
      { name: 'vehicles_year_idx', fields: ['year'] },
      { name: 'vehicles_price_currency_idx', fields: ['price', 'currency'] },
      { name: 'vehicles_location_idx', fields: ['location_country', 'location_region'] },
    ],
  }
);

/** Static constants + flags used by the service, routes and migration 001. */
Vehicle.STATUSES = STATUSES;
Vehicle.PUBLIC_STATUS = 'active';
Vehicle.MILEAGE_UNITS = MILEAGE_UNITS;
Vehicle.SUPPORTED_CURRENCIES = SUPPORTED_CURRENCIES;
Vehicle.SORT_OPTIONS = SORT_OPTIONS;
Vehicle.migrationManaged = true;

module.exports = Vehicle;
module.exports.STATUSES = STATUSES;
module.exports.PUBLIC_STATUS = 'active';
module.exports.MILEAGE_UNITS = MILEAGE_UNITS;
module.exports.SUPPORTED_CURRENCIES = SUPPORTED_CURRENCIES;
module.exports.SORT_OPTIONS = SORT_OPTIONS;
