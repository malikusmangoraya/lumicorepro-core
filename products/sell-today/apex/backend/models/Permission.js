import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Permission extends Model {}

Permission.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    code: {
      type: DataTypes.STRING(80),
      allowNull: false,
      unique: true,
      validate: {
        is: /^[a-z][a-z0-9_.]*$/,
      },
    },
    name: {
      type: DataTypes.STRING(120),
      allowNull: false,
    },
    description: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
  },
  {
    sequelize,
    modelName: 'Permission',
    tableName: 'permissions',
    timestamps: true,
  }
);

export default Permission;
