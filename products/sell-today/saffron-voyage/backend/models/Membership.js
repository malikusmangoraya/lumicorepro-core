import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Membership extends Model {}

Membership.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    org_id: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
    user_id: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
    role_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
    status: {
      type: DataTypes.STRING(20),
      allowNull: false,
      defaultValue: 'active',
      validate: {
        isIn: { args: [['invited', 'active', 'revoked']], msg: 'Invalid membership status' },
      },
    },
    invited_by: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
    joined_at: {
      type: DataTypes.DATE,
      allowNull: true,
    },
  },
  {
    sequelize,
    modelName: 'Membership',
    tableName: 'memberships',
    timestamps: true,
    indexes: [
      { unique: true, fields: ['org_id', 'user_id'] },
      { fields: ['user_id'] },
      { fields: ['role_id'] },
    ],
  }
);

export default Membership;
