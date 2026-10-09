import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * LicenseEntitlement — purchase → activation record, created from Lemon
 * Squeezy webhooks. The license key engine is stateless HMAC; this table adds
 * the mutable part (who activated what, from which order, and whether the
 * subscription is still alive), which is what makes revocation possible.
 */
const LicenseEntitlement = sequelize.define(
  'LicenseEntitlement',
  {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    license_key: { type: DataTypes.STRING(255), allowNull: false, unique: true },
    variant_name: { type: DataTypes.STRING(120), allowNull: true },
    order_id: { type: DataTypes.STRING(64), allowNull: true },
    store_id: { type: DataTypes.STRING(64), allowNull: true },
    customer_email: { type: DataTypes.STRING(255), allowNull: true },
    customer_name: { type: DataTypes.STRING(255), allowNull: true },
    // active | revoked | paused | rejected
    status: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'active' },
    license_valid: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false },
    license_status: { type: DataTypes.STRING(30), allowNull: true },
    activated_at: { type: DataTypes.DATE, allowNull: true },
    expires_at: { type: DataTypes.DATE, allowNull: true },
    created_at: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW },
  },
  {
    tableName: 'license_entitlements',
    timestamps: false,
    updatedAt: false,
    indexes: [
      { fields: ['status'] },
      { fields: ['order_id'] },
    ],
  },
);

export default LicenseEntitlement;