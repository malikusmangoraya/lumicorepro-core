import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * AI Spend Ledger — one row per billable AI run.
 *
 * Estimates exist elsewhere (usageGuard counters, spendEstimator); this is the
 * per-run ledger the finance/compliance side needs: which user, which run, how
 * many tokens, at what estimated cost. Append-only by convention (no updates,
 * no deletes; corrections are new rows with `kind: 'adjustment'`).
 */
const AiSpendLedger = sequelize.define(
  'AiSpendLedger',
  {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    run_id: { type: DataTypes.STRING(64), allowNull: true },
    user_id: { type: DataTypes.INTEGER, allowNull: true },
    org_id: { type: DataTypes.INTEGER, allowNull: true },
    ip: { type: DataTypes.STRING(45), allowNull: true },
    endpoint: { type: DataTypes.STRING(50), allowNull: false, defaultValue: 'generation' },
    provider: { type: DataTypes.STRING(50), allowNull: true },
    model: { type: DataTypes.STRING(100), allowNull: true },
    estimated_tokens: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
    estimated_cost_usd: { type: DataTypes.DECIMAL(12, 6), allowNull: false, defaultValue: 0 },
    kind: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'run' },
    created_at: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW },
  },
  {
    tableName: 'ai_spend_ledger',
    timestamps: false,
    updatedAt: false,
    indexes: [
      { fields: ['user_id', 'created_at'] },
      { fields: ['run_id'] },
      { fields: ['endpoint', 'created_at'] },
    ],
  },
);

export default AiSpendLedger;
