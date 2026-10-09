import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Coupon extends Model {}

Coupon.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    code: {
      type: DataTypes.STRING(50),
      allowNull: false,
      unique: true,
      validate: {
        notEmpty: { msg: 'Coupon code is required' },
      },
    },
    type: {
      type: DataTypes.STRING(20),
      defaultValue: 'percentage',
      validate: {
        isIn: { args: [['percentage', 'fixed', 'free_shipping']], msg: 'Invalid coupon type' },
      },
    },
    value: {
      type: DataTypes.DECIMAL(10, 2),
      defaultValue: 0,
      comment: 'Percent (0-100) for percentage, amount for fixed',
    },
    minSubtotal: {
      type: DataTypes.DECIMAL(10, 2),
      defaultValue: 0,
      comment: 'Minimum cart subtotal required to use this coupon',
    },
    maxDiscount: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: true,
      comment: 'Cap on discount amount (optional)',
    },
    usageLimit: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
      comment: '0 = unlimited total redemptions',
    },
    usageCount: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
    },
    perUserLimit: {
      type: DataTypes.INTEGER,
      defaultValue: 1,
    },
    appliesTo: {
      type: DataTypes.JSONB,
      defaultValue: {},
      comment: 'Optional { category_ids: [], product_ids: [] } restrictions',
    },
    startsAt: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    expiresAt: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    isActive: {
      type: DataTypes.BOOLEAN,
      defaultValue: true,
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
    modelName: 'Coupon',
    tableName: 'coupons',
    timestamps: true,
  }
);

export default Coupon;
