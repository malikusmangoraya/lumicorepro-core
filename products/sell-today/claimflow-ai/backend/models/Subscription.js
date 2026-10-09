import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Subscription extends Model {}

Subscription.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    user_id: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
    planName: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    plan_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
    stripeSubscriptionId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      comment: 'Stripe Subscription object id (sub_...)',
    },
    stripeCustomerId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    priceId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      comment: 'Stripe Price id (price_...)',
    },
    status: {
      type: DataTypes.STRING(50),
      defaultValue: 'active',
      validate: {
        isIn: {
          args: [
            ['active', 'canceled', 'cancelled', 'past_due', 'trialing', 'incomplete', 'unpaid'],
          ],
          msg: 'Invalid subscription status',
        },
      },
    },
    cancelAtPeriodEnd: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    trialEnd: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    currentPeriodStart: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    currentPeriodEnd: {
      type: DataTypes.DATE,
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
    modelName: 'Subscription',
    tableName: 'subscriptions',
    timestamps: true,
  }
);

export default Subscription;
