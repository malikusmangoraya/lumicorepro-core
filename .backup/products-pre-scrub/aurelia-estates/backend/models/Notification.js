import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Notification extends Model {}

Notification.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    recipient: {
      type: DataTypes.INTEGER,
      allowNull: false,
      field: 'recipient_id',
    },
    type: {
      type: DataTypes.STRING(50),
      defaultValue: 'info',
      validate: {
        isIn: {
          args: [
            ['info', 'success', 'warning', 'error', 'order', 'payment', 'system', 'social_proof'],
          ],
          msg: 'Invalid notification type',
        },
      },
    },
    title: {
      type: DataTypes.STRING(255),
      allowNull: false,
    },
    message: {
      type: DataTypes.TEXT,
      allowNull: false,
    },
    link: {
      type: DataTypes.STRING(500),
      defaultValue: '',
    },
    read: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    readAt: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    metadata: {
      type: DataTypes.JSONB,
      defaultValue: {},
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
    modelName: 'Notification',
    tableName: 'notifications',
    timestamps: true,
  }
);

export default Notification;
