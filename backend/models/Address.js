import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Address extends Model {}

Address.init(
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
    name: {
      type: DataTypes.STRING(255),
      allowNull: false,
    },
    phone: {
      type: DataTypes.STRING(50),
      defaultValue: '',
    },
    address_line1: {
      type: DataTypes.STRING(255),
      allowNull: false,
    },
    address_line2: {
      type: DataTypes.STRING(255),
      defaultValue: '',
    },
    city: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    state: {
      type: DataTypes.STRING(100),
      defaultValue: '',
    },
    postal_code: {
      type: DataTypes.STRING(20),
      defaultValue: '',
    },
    country: {
      type: DataTypes.STRING(100),
      defaultValue: 'US',
    },
    is_default: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    label: {
      type: DataTypes.STRING(50),
      defaultValue: 'shipping',
      validate: {
        isIn: { args: [['shipping', 'billing']], msg: 'Invalid address label' },
      },
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
    modelName: 'Address',
    tableName: 'addresses',
    timestamps: true,
  }
);

export default Address;