'use strict';

/**
 * 003 — buyer enquiries.
 *
 * Creates `inquiries` with foreign keys to the vehicle being asked about and the
 * authenticated buyer (where one exists), plus the indexes the staff queue needs.
 *
 * Both foreign keys are nullable and `ON DELETE SET NULL`: an anonymous enquiry
 * has no user, and removing a user or a vehicle must never cascade away the
 * dealership's lead history.
 *
 * The `tableExists` guard keeps `up` safe where the table already exists.
 *
 * @type {import('umzug').Migration}
 */
const { DataTypes } = require('sequelize');

const TABLE = 'inquiries';

module.exports = {
  async up({ context: queryInterface }) {
    if (await queryInterface.tableExists(TABLE)) return;

    await queryInterface.createTable(TABLE, {
      id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true, allowNull: false },
      vehicle_id: {
        type: DataTypes.INTEGER,
        allowNull: true,
        references: { model: 'vehicles', key: 'id' },
        onDelete: 'SET NULL',
        onUpdate: 'CASCADE',
      },
      user_id: {
        type: DataTypes.INTEGER,
        allowNull: true,
        references: { model: 'users', key: 'id' },
        onDelete: 'SET NULL',
        onUpdate: 'CASCADE',
      },
      name: { type: DataTypes.STRING(120), allowNull: false },
      email: { type: DataTypes.STRING(160), allowNull: false },
      phone: { type: DataTypes.STRING(40), allowNull: true },
      message: { type: DataTypes.TEXT, allowNull: false },
      locale: { type: DataTypes.STRING(10), allowNull: true },
      consent_given: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false },
      consent_at: { type: DataTypes.DATE, allowNull: true },
      status: { type: DataTypes.STRING(24), allowNull: false, defaultValue: 'new' },
      idempotency_key: { type: DataTypes.STRING(80), allowNull: true, unique: true },
      admin_notes: { type: DataTypes.TEXT, allowNull: true },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });

    await queryInterface.addIndex(TABLE, ['status'], { name: 'inquiries_status_idx' });
    await queryInterface.addIndex(TABLE, ['vehicle_id'], { name: 'inquiries_vehicle_idx' });
    await queryInterface.addIndex(TABLE, ['user_id'], { name: 'inquiries_user_idx' });
    await queryInterface.addIndex(TABLE, ['created_at'], { name: 'inquiries_created_idx' });
  },

  async down({ context: queryInterface }) {
    await queryInterface.dropTable(TABLE).catch(() => {});
  },
};
