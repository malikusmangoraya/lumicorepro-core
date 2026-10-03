import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Order extends Model {}

Order.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    user_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
    org_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      comment: 'Owning organization (multi-tenant); null = legacy single-tenant',
      references: { model: 'organizations', key: 'id' },
      onDelete: 'SET NULL',
      onUpdate: 'CASCADE',
    },
    orderNumber: {
      type: DataTypes.STRING(50),
      unique: true,
      allowNull: false,
    },
    shippingAddress: {
      type: DataTypes.JSONB,
      allowNull: false,
    },
    billingAddress: {
      type: DataTypes.JSONB,
      allowNull: true,
    },
    paymentMethod: {
      type: DataTypes.STRING(50),
      allowNull: false,
      defaultValue: 'stripe',
      validate: {
        isIn: { args: [['stripe', 'paypal', 'credit_card', 'cod']], msg: 'Invalid payment method' },
      },
    },
    paymentResult: {
      type: DataTypes.JSONB,
      allowNull: true,
    },
    itemsPrice: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      defaultValue: 0,
    },
    taxPrice: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      defaultValue: 0,
    },
    shippingPrice: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      defaultValue: 0,
    },
    discountAmount: {
      type: DataTypes.DECIMAL(10, 2),
      defaultValue: 0,
    },
    totalPrice: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      defaultValue: 0,
    },
    currency: {
      type: DataTypes.STRING(10),
      defaultValue: 'USD',
    },
    isPaid: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    paidAt: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    isDelivered: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    deliveredAt: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    status: {
      type: DataTypes.STRING(50),
      defaultValue: 'pending',
      validate: {
        isIn: { args: [['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']], msg: 'Invalid order status' },
      },
    },
    trackingNumber: {
      type: DataTypes.STRING(100),
      defaultValue: '',
    },
    carrier: {
      type: DataTypes.STRING(100),
      defaultValue: '',
    },
    items: {
      type: DataTypes.JSONB,
      allowNull: false,
      defaultValue: [],
      comment: 'Array of order line items: [{product_id, title, price, quantity, image, selectedColor, selectedSize}]',
    },
    notes: {
      type: DataTypes.TEXT,
      defaultValue: '',
    },
    deleted_at: {
      type: DataTypes.DATE,
      allowNull: true,
      comment: 'Soft-delete marker (paranoid)',
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
    modelName: 'Order',
    tableName: 'orders',
    timestamps: true,
    paranoid: true,
    deletedAt: 'deleted_at',
    indexes: [
      { name: 'idx_orders_org', fields: ['org_id'] },
      { name: 'idx_orders_org_status', fields: ['org_id', 'status'] },
      { name: 'idx_orders_status', fields: ['status'] },
      { name: 'idx_orders_user', fields: ['user_id'] },
      { name: 'idx_orders_created_at', fields: ['createdAt'] },
      { name: 'idx_orders_deleted_at', fields: ['deleted_at'] },
    ],
  }
);

export default Order;
