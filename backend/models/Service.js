import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

const Service = sequelize.define('Service', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  name: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  slug: {
    type: DataTypes.STRING(255),
    unique: true,
  },
  description: {
    type: DataTypes.TEXT,
    defaultValue: '',
  },
  category: {
    type: DataTypes.STRING(100),
    defaultValue: 'general',
  },
  duration: {
    type: DataTypes.INTEGER,
    defaultValue: 30,
  },
  price: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false,
  },
  depositRequired: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  isActive: {
    type: DataTypes.BOOLEAN,
    defaultValue: true,
  },
}, {
  tableName: 'services',
  timestamps: true,
  hooks: {
    beforeSave: (service) => {
      if (service.changed('name') && !service.slug) {
        service.slug = service.name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/(^-|-$)/g, '');
      }
    },
  },
});

export default Service;
