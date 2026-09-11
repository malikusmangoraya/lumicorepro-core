import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * Durable ledger of processed payment webhook events.
 * `event_id` is UNIQUE, so concurrent deliveries / Redis evictions can never
 * double-apply a webhook: processing is safe to replay against this table.
 */
class WebhookEvent extends Model {}

WebhookEvent.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    event_id: {
      type: DataTypes.STRING(255),
      allowNull: false,
      unique: true,
    },
    gateway: {
      type: DataTypes.STRING(50),
      allowNull: false,
      defaultValue: 'stripe',
    },
    event_type: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    status: {
      type: DataTypes.STRING(20),
      allowNull: false,
      defaultValue: 'processed',
      validate: {
        isIn: { args: [['processed', 'failed']], msg: 'Invalid webhook event status' },
      },
    },
    payload: {
      type: DataTypes.JSONB,
      allowNull: true,
    },
    createdAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
    updatedAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
  },
  {
    sequelize,
    modelName: 'WebhookEvent',
    tableName: 'webhook_events',
    timestamps: true,
    indexes: [{ unique: true, fields: ['event_id'] }, { fields: ['gateway'] }],
  }
);

export default WebhookEvent;