import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Plan extends Model {}

Plan.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    name: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    slug: {
      type: DataTypes.STRING(100),
      allowNull: false,
      unique: true,
    },
    description: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    stripeProductId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    stripePriceId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    amount: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      defaultValue: 0,
    },
    currency: {
      type: DataTypes.STRING(10),
      defaultValue: 'usd',
    },
    interval: {
      type: DataTypes.STRING(20),
      allowNull: true,
      comment: 'month | year | one_time',
    },
    creditsGrant: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: true,
      defaultValue: 0,
      comment: 'AI agent credits granted on purchase',
    },
    features: {
      type: DataTypes.JSONB,
      defaultValue: [],
      comment: 'Feature list rendered on the pricing card',
    },
    highlight: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
      comment: 'Mark as the recommended plan',
    },
    isActive: {
      type: DataTypes.BOOLEAN,
      defaultValue: true,
    },
    sortOrder: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
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
    modelName: 'Plan',
    tableName: 'plans',
    timestamps: true,
  }
);

export default Plan;