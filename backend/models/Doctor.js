import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

const Doctor = sequelize.define('Doctor', {
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
  specialty: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  subSpecialty: {
    type: DataTypes.STRING(255),
    defaultValue: '',
  },
  email: {
    type: DataTypes.STRING(255),
    allowNull: false,
    unique: true,
  },
  phone: {
    type: DataTypes.STRING(20),
    defaultValue: '',
  },
  avatar: {
    type: DataTypes.STRING(500),
    defaultValue: '',
  },
  bio: {
    type: DataTypes.TEXT,
    defaultValue: '',
  },
  qualifications: {
    type: DataTypes.JSONB,
    defaultValue: [],
  },
  experience: {
    type: DataTypes.INTEGER,
    defaultValue: 0,
  },
  rating: {
    type: DataTypes.DECIMAL(3, 2),
    defaultValue: 0,
  },
  reviewCount: {
    type: DataTypes.INTEGER,
    defaultValue: 0,
  },
  consultationFee: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false,
  },
  depositRequired: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  workingHours: {
    type: DataTypes.JSONB,
    defaultValue: {
      monday: { start: '09:00', end: '17:00' },
      tuesday: { start: '09:00', end: '17:00' },
      wednesday: { start: '09:00', end: '17:00' },
      thursday: { start: '09:00', end: '17:00' },
      friday: { start: '09:00', end: '17:00' },
      saturday: null,
      sunday: null,
    },
  },
  slotDuration: {
    type: DataTypes.INTEGER,
    defaultValue: 30,
  },
  isActive: {
    type: DataTypes.BOOLEAN,
    defaultValue: true,
  },
  org_id: {
    type: DataTypes.BIGINT.UNSIGNED,
    allowNull: true,
  },
}, {
  tableName: 'doctors',
  timestamps: true,
  hooks: {
    beforeSave: (doctor) => {
      if (doctor.changed('name') && !doctor.slug) {
        doctor.slug = doctor.name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/(^-|-$)/g, '');
      }
    },
  },
});

export default Doctor;
