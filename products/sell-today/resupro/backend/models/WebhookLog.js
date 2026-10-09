import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * Audit trail of every webhook delivery attempt.
 *
 * Rows older than 30 days are removed by a periodic cleanup (see
 * `scripts/prune-webhook-logs`), which replaces the TTL index a document store
 * would have given us.
 */
class WebhookLog extends Model {}

WebhookLog.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    source: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    event: {
      type: DataTypes.STRING(150),
      allowNull: false,
    },
    payload: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    status: {
      type: DataTypes.STRING(30),
      allowNull: false,
      defaultValue: 'received',
    },
    attempts: {
      type: DataTypes.INTEGER,
      allowNull: false,
      defaultValue: 0,
    },
    error: {
      type: DataTypes.TEXT,
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
    modelName: 'WebhookLog',
    tableName: 'webhook_logs',
    timestamps: true,
    indexes: [
      { fields: ['source'] },
      { fields: ['event'] },
      { fields: ['createdAt'] },
      { fields: ['source', 'event', 'createdAt'] },
    ],
  }
);

export default WebhookLog;
