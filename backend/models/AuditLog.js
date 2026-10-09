import crypto from 'crypto';
import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * Canonical audit-row representation that the chain hash covers.
 * Order matters: changing this changes every recomputed hash, so treat it as
 * schema (verify uses the same function).
 */
export function canonicalAuditRow(row) {
  return [
    row.prev_hash || '',
    row.user_id ?? '',
    row.email ?? '',
    row.action ?? '',
    row.ip ?? '',
    row.user_agent ?? '',
    row.meta ? JSON.stringify(row.meta) : '',
    row.created_at ? new Date(row.created_at).toISOString() : '',
  ].join('|');
}

export function computeAuditHash(row) {
  return crypto.createHash('sha256').update(canonicalAuditRow(row)).digest('hex');
}

/**
 * Recompute the whole chain and report the first break, if any.
 * Rows are ordered by created_at, id — the same order create() chains them.
 */
export async function verifyAuditChain(model = AuditLog, limit = 5000) {
  const rows = await model.findAll({
    order: [['created_at', 'ASC'], ['id', 'ASC']],
    limit,
    raw: true,
  });
  let prevHash = '';
  for (const row of rows) {
    if ((row.prev_hash || '') !== prevHash) {
      return { valid: false, brokenAtId: row.id, reason: 'prev_hash does not match the previous row' };
    }
    const expected = computeAuditHash(row);
    if (row.hash !== expected) {
      return { valid: false, brokenAtId: row.id, reason: 'row hash mismatch (row was modified)' };
    }
    prevHash = row.hash;
  }
  return { valid: true, checked: rows.length, headHash: prevHash };
}

const AuditLog = sequelize.define(
  'AuditLog',
  {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: true },
    email: { type: DataTypes.STRING(255), allowNull: true },
    action: { type: DataTypes.STRING(100), allowNull: false },
    ip: { type: DataTypes.STRING(45), allowNull: true },
    user_agent: { type: DataTypes.STRING(255), allowNull: true },
    meta: { type: DataTypes.JSON, allowNull: true },
    prev_hash: { type: DataTypes.STRING(64), allowNull: true },
    hash: { type: DataTypes.STRING(64), allowNull: true },
    created_at: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW },
  },
  {
    tableName: 'audit_logs',
    timestamps: true,
    updatedAt: false,
    indexes: [
      { fields: ['action', 'created_at'] },
      { fields: ['user_id', 'created_at'] },
    ],
    hooks: {
      beforeValidate: async (entry) => {
        // Hash chain: hash(n) = sha256(prev_hash(n-1) || canonical(row n)).
        // Only sealed on INSERT: updates must never touch the chain (and must
        // not hit the DB to resolve it — beforeUpdate rejects them anyway).
        if (entry.hash || !entry.isNewRecord) return;
        let prevHash = entry.prev_hash || '';
        if (!prevHash) {
          const [last] = await AuditLog.findAll({
            order: [['created_at', 'DESC'], ['id', 'DESC']],
            limit: 1,
            attributes: ['hash'],
            raw: true,
          });
          prevHash = last?.hash || '';
        }
        entry.prev_hash = prevHash;
        entry.hash = computeAuditHash({
          ...entry.get({ plain: true }),
          prev_hash: prevHash,
        });
      },
      // Append-only trail: routine code must never rewrite or delete history.
      // Retention purges go through purgeAuditLogs() (raw query, admin-only
      // route) which deliberately bypasses these hooks.
      beforeUpdate: () => {
        throw new Error('AuditLog is immutable: updates are forbidden');
      },
      beforeDestroy: () => {
        throw new Error('AuditLog is immutable: deletes are forbidden');
      },
    },
  }
);

/**
 * Retention purge — the ONLY sanctioned delete path. Uses a raw query so the
 * immutability hooks above do not fire. Call only from the admin retention
 * route after explicit confirmation.
 */
export async function purgeAuditLogs(beforeDate, db = sequelize) {
  const [, metadata] = await db.query('DELETE FROM audit_logs WHERE created_at < :before', {
    replacements: { before: beforeDate },
  });
  return Number(metadata?.rowCount ?? 0);
}

export default AuditLog;
