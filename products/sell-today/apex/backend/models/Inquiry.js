/**
 * Inquiry — a buyer's message about a vehicle (or the dealership generally).
 *
 * Anonymous enquiries are allowed, so both `vehicle_id` and `user_id` are
 * nullable. `user_id` is only ever set from a verified session, never from a
 * request body: that binding is what makes "my enquiries" safe to scope.
 *
 * `idempotency_key` carries a client-generated token so a double-submitted lead
 * form cannot create two leads. It is nullable and unique — both PostgreSQL and
 * SQLite allow many NULLs in a unique index.
 *
 * `migrationManaged = true` keeps the baseline migration (001) away from this
 * table so migration 003 owns its DDL, indexes and rollback.
 */
const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const STATUSES = ['new', 'contacted', 'viewing_scheduled', 'closed', 'spam'];
const MIN_MESSAGE = 10;
const MAX_MESSAGE = 4000;

const Inquiry = sequelize.define(
  'Inquiry',
  {
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    vehicle_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      validate: { min: { args: [1], msg: 'vehicle_id must be a positive id' } },
    },
    user_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      validate: { min: { args: [1], msg: 'user_id must be a positive id' } },
    },
    name: {
      type: DataTypes.STRING(120),
      allowNull: false,
      validate: {
        notEmpty: { msg: 'name is required' },
        len: { args: [2, 120], msg: 'name must be between 2 and 120 characters' },
      },
    },
    email: {
      type: DataTypes.STRING(160),
      allowNull: false,
      validate: {
        notEmpty: { msg: 'email is required' },
        isEmail: { msg: 'email must be a valid address' },
      },
      set(value) {
        this.setDataValue('email', String(value || '').trim().toLowerCase());
      },
    },
    phone: { type: DataTypes.STRING(40), allowNull: true },
    message: {
      type: DataTypes.TEXT,
      allowNull: false,
      validate: {
        notEmpty: { msg: 'message is required' },
        len: {
          args: [MIN_MESSAGE, MAX_MESSAGE],
          msg: `message must be between ${MIN_MESSAGE} and ${MAX_MESSAGE} characters`,
        },
      },
    },
    locale: { type: DataTypes.STRING(10), allowNull: true },
    consent_given: {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false,
      validate: {
        /** Storage and legal record both require an explicit, recorded opt-in. */
        consentProvided(value) {
          if (value !== true) throw new Error('privacy consent is required');
        },
      },
    },
    consent_at: { type: DataTypes.DATE, allowNull: true },
    status: {
      type: DataTypes.STRING(24),
      allowNull: false,
      defaultValue: 'new',
      validate: { isIn: { args: [STATUSES], msg: 'status is not a known enquiry state' } },
    },
    idempotency_key: { type: DataTypes.STRING(80), allowNull: true, unique: true },
    admin_notes: { type: DataTypes.TEXT, allowNull: true },
  },
  {
    tableName: 'inquiries',
    timestamps: true,
    underscored: true,
    createdAt: 'created_at',
    updatedAt: 'updated_at',
    indexes: [
      { name: 'inquiries_status_idx', fields: ['status'] },
      { name: 'inquiries_vehicle_idx', fields: ['vehicle_id'] },
      { name: 'inquiries_user_idx', fields: ['user_id'] },
      { name: 'inquiries_created_idx', fields: ['created_at'] },
    ],
  }
);

Inquiry.STATUSES = STATUSES;
Inquiry.MIN_MESSAGE = MIN_MESSAGE;
Inquiry.MAX_MESSAGE = MAX_MESSAGE;
Inquiry.migrationManaged = true;

module.exports = Inquiry;
module.exports.STATUSES = STATUSES;
module.exports.MIN_MESSAGE = MIN_MESSAGE;
module.exports.MAX_MESSAGE = MAX_MESSAGE;
