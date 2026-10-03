import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Organization extends Model {}

Organization.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    name: {
      type: DataTypes.STRING(255),
      allowNull: false,
      validate: {
        notEmpty: { msg: 'Please provide an organization name' },
      },
    },
    slug: {
      type: DataTypes.STRING(120),
      allowNull: false,
      unique: true,
      validate: {
        is: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
      },
    },
    owner_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      comment: 'Creator/owner user id',
    },
    settings: {
      type: DataTypes.JSONB,
      allowNull: true,
      defaultValue: {},
    },
    deleted_at: {
      type: DataTypes.DATE,
      allowNull: true,
      comment: 'Soft-delete marker',
    },
  },
  {
    sequelize,
    modelName: 'Organization',
    tableName: 'organizations',
    timestamps: true,
    paranoid: true,
    // Sequelize defaults the paranoid column to "deletedAt"; this schema stores it
    // as `deleted_at` (AGENTS.md DB rule), so `destroy()` must write that column.
    deletedAt: 'deleted_at',
    indexes: [{ fields: ['slug'] }, { fields: ['owner_id'] }, { fields: ['deleted_at'] }],
  }
);

export default Organization;