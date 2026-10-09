import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Payment extends Model {}

Payment.init(
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
    order_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
    provider: {
      type: DataTypes.STRING(50),
      defaultValue: 'stripe',
      validate: {
        isIn: {
          args: [['stripe', 'paypal', 'razorpay', 'cashfree', 'payme', 'paddle', 'cod', 'other']],
          msg: 'Invalid payment provider',
        },
      },
    },
    stripePaymentIntentId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      unique: true,
    },
    stripeChargeId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    // Unified gateway payment reference used by stripe.service.js webhook handler
    gatewayPaymentId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      comment: 'Provider-agnostic payment ID set on webhook confirmation',
    },
    paypalPayerId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    paypalOrderId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      unique: true,
    },
    razorpayPaymentId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    razorpayOrderId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    cashfreePaymentId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      unique: true,
    },
    cashfreeOrderId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    paymePaymentId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    amount: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      validate: {
        min: { args: [0], msg: 'Payment amount must be non-negative' },
      },
    },
    currency: {
      type: DataTypes.STRING(10),
      defaultValue: 'usd',
    },
    status: {
      type: DataTypes.STRING(50),
      defaultValue: 'pending',
      validate: {
        isIn: {
          args: [['pending', 'processing', 'succeeded', 'failed', 'cancelled', 'refunded']],
          msg: 'Invalid payment status',
        },
      },
    },
    paymentMethod: {
      type: DataTypes.STRING(50),
      defaultValue: 'card',
    },
    cardDetails: {
      type: DataTypes.JSONB,
      allowNull: true,
    },
    receiptUrl: {
      type: DataTypes.STRING(500),
      defaultValue: '',
    },
    errorMessage: {
      type: DataTypes.TEXT,
      defaultValue: '',
    },
    refundAmount: {
      type: DataTypes.DECIMAL(10, 2),
      defaultValue: 0,
    },
    refundReason: {
      type: DataTypes.TEXT,
      defaultValue: '',
    },
    providerResponse: {
      type: DataTypes.JSONB,
      allowNull: true,
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
    modelName: 'Payment',
    tableName: 'payments',
    timestamps: true,
  }
);

export default Payment;
