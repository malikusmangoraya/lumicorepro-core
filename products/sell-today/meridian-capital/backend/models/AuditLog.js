import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

const AuditLog = sequelize.define(
  'AuditLog',
  {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.BIGINT.UNSIGNED, allowNull: true },
    email: { type: DataTypes.STRING(255), allowNull: true },
    action: { type: DataTypes.STRING(100), allowNull: false },
    ip: { type: DataTypes.STRING(45), allowNull: true },
    user_agent: { type: DataTypes.STRING(255), allowNull: true },
    meta: { type: DataTypes.JSON, allowNull: true },
    created_at: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW },
  },
  {
    tableName: 'audit_logs',
    timestamps: true,
    updatedAt: false,
    indexes: [{ fields: ['action', 'created_at'] }, { fields: ['user_id', 'created_at'] }],
  }
);

export default AuditLog;
