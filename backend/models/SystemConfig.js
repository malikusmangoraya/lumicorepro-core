import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * SystemConfig — runtime-managed configuration store (no-code admin panel).
 *
 * Key→JSON value pairs persisted in PostgreSQL (mirrored to a runtime cache).
 * Managed groups (all set from the Admin → Global System Settings panel):
 *   - business   : { name, logoUrl, supportEmail, tagline }
 *   - currency   : { code, symbol }
 *   - payments   : { stripe: { enabled, mode, secretKey, publishableKey, webhookSecret },
 *                    paypal: { enabled, mode, clientId, clientSecret, webhookId } }
 *   - smtp       : { enabled, host, port, secure, user, pass, fromName, fromEmail }
 *   - setup      : { completed, completedAt, superAdminEmail }
 */
class SystemConfig extends Model {}

SystemConfig.init(
  {
    key: {
      type: DataTypes.STRING(50),
      primaryKey: true,
    },
    value: {
      type: DataTypes.JSONB,
      allowNull: false,
      defaultValue: {},
    },
  },
  {
    sequelize,
    modelName: 'SystemConfig',
    tableName: 'system_configs',
    timestamps: true,
  }
);

export default SystemConfig;