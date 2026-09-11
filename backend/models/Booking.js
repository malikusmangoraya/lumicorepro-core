import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

const Booking = sequelize.define('Booking', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  user_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: { model: 'users', key: 'id' },
  },
  doctor_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: { model: 'doctors', key: 'id' },
  },
  service_id: {
    type: DataTypes.INTEGER,
    allowNull: true,
    references: { model: 'services', key: 'id' },
  },
  bookingNumber: {
    type: DataTypes.STRING(50),
    unique: true,
    allowNull: false,
  },
  date: {
    type: DataTypes.DATEONLY,
    allowNull: false,
  },
  time: {
    type: DataTypes.STRING(5),
    allowNull: false,
  },
  duration: {
    type: DataTypes.INTEGER,
    defaultValue: 30,
  },
  status: {
    type: DataTypes.ENUM('pending', 'confirmed', 'cancelled', 'completed', 'no-show'),
    defaultValue: 'pending',
  },
  reason: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  notes: {
    type: DataTypes.TEXT,
    defaultValue: '',
  },
  patientInfo: {
    type: DataTypes.JSONB,
    allowNull: false,
  },
  paymentStatus: {
    type: DataTypes.ENUM('pending', 'deposit_paid', 'paid', 'refunded'),
    defaultValue: 'pending',
  },
  depositAmount: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  totalAmount: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  cancelledAt: {
    type: DataTypes.DATE,
    allowNull: true,
  },
  cancellationReason: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
}, {
  tableName: 'bookings',
  timestamps: true,
  hooks: {
    beforeCreate: (booking) => {
      if (!booking.bookingNumber) {
        const date = new Date();
        const ds = date.toISOString().slice(0, 10).replace(/-/g, '');
        const rand = Math.random().toString(36).substring(2, 7).toUpperCase();
        booking.bookingNumber = `BK-${ds}-${rand}`;
      }
    },
  },
});

export default Booking;
