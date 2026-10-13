'use strict';

/**
 * 002 — Apex-owned vehicle inventory.
 *
 * Creates `vehicles`, the authoritative record of what the dealership owns and
 * is willing to show. The table is created here (not by the 001 baseline) so it
 * carries its own indexes and constraints and can be rolled back on its own.
 *
 * The `tableExists` guard keeps `up` safe on an environment where the table was
 * already created by an earlier baseline run (`001` skips migration-managed
 * models going forward, but databases created before that fix still have it).
 *
 * CHECK constraints for `status` / `mileage_unit` / `currency` are intentionally
 * not added: SQLite cannot add constraints to an existing table, and the model
 * plus the service validate these values on every write for both dialects.
 *
 * @type {import('umzug').Migration}
 */
const { DataTypes } = require('sequelize');

const TABLE = 'vehicles';

module.exports = {
  async up({ context: queryInterface }) {
    if (await queryInterface.tableExists(TABLE)) return;

    await queryInterface.createTable(TABLE, {
      id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true, allowNull: false },
      slug: { type: DataTypes.STRING(160), allowNull: false, unique: true },
      make: { type: DataTypes.STRING(80), allowNull: false },
      model: { type: DataTypes.STRING(120), allowNull: false },
      year: { type: DataTypes.INTEGER, allowNull: false },
      title: { type: DataTypes.STRING(200), allowNull: false },
      description: { type: DataTypes.TEXT, allowNull: true },
      price: { type: DataTypes.DECIMAL(14, 2), allowNull: false },
      currency: { type: DataTypes.STRING(3), allowNull: false },
      mileage: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
      mileage_unit: { type: DataTypes.STRING(2), allowNull: false, defaultValue: 'km' },
      body_style: { type: DataTypes.STRING(40), allowNull: true },
      fuel_type: { type: DataTypes.STRING(40), allowNull: true },
      transmission: { type: DataTypes.STRING(40), allowNull: true },
      location_country: { type: DataTypes.STRING(2), allowNull: false },
      location_region: { type: DataTypes.STRING(120), allowNull: true },
      status: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'draft' },
      media: { type: DataTypes.JSON, allowNull: true },
      inspection_references: { type: DataTypes.JSON, allowNull: true },
      provenance_verified: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false },
      condition_notes: { type: DataTypes.TEXT, allowNull: true },
      condition_report_url: { type: DataTypes.STRING(500), allowNull: true },
      vin: { type: DataTypes.STRING(17), allowNull: true },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });

    await queryInterface.addIndex(TABLE, ['status'], { name: 'vehicles_status_idx' });
    await queryInterface.addIndex(TABLE, ['make', 'model'], { name: 'vehicles_make_model_idx' });
    await queryInterface.addIndex(TABLE, ['year'], { name: 'vehicles_year_idx' });
    await queryInterface.addIndex(TABLE, ['price', 'currency'], { name: 'vehicles_price_currency_idx' });
    await queryInterface.addIndex(TABLE, ['location_country', 'location_region'], {
      name: 'vehicles_location_idx',
    });
  },

  async down({ context: queryInterface }) {
    await queryInterface.dropTable(TABLE).catch(() => {});
  },
};
