import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class FeatureFlag extends Model {}

FeatureFlag.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    key: {
      type: DataTypes.STRING(100),
      allowNull: false,
      unique: true,
      validate: {
        is: /^[a-z0-9]+(?:[._-][a-z0-9]+)*$/,
      },
    },
    enabled: {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false,
    },
    rollout: {
      type: DataTypes.INTEGER,
      allowNull: false,
      defaultValue: 100,
      validate: { min: 0, max: 100 },
      comment: 'Percentage 0-100 of users who get the flag when enabled',
    },
    description: {
      type: DataTypes.STRING(500),
      defaultValue: '',
    },
  },
  {
    sequelize,
    modelName: 'FeatureFlag',
    tableName: 'feature_flags',
    timestamps: true,
  }
);

export default FeatureFlag;
