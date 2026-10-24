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
  org_id: {
    type: DataTypes.INTEGER,
    allowNull: true,
    comment: 'Owning organization (multi-tenant); null = legacy single-tenant',
    references: { model: 'organizations', key: 'id' },
    onDelete: 'SET NULL',
    onUpdate: 'CASCADE',
  },
  doctor_id: {
    type: DataTypes.INTEGER,
    // Healthcare bookings always carry one; a restaurant table booking has no
    // doctor, and routes/restaurant.routes.js writes the same table.
    allowNull: true,
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
  startAt: {
    type: DataTypes.DATE,
    allowNull: true,
    comment: 'Slot as an unambiguous instant (DATEONLY + local time cannot be ordered or compared across timezones)',
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
    allowNull: true,
  },
  notes: {
    type: DataTypes.TEXT,
    defaultValue: '',
  },
  patientInfo: {
    type: DataTypes.JSONB,
    // Healthcare bookings always carry it; a restaurant table booking stores the
    // diner in `metadata` instead. routes/booking.routes.js still requires it
    // from the request body, so an appointment can never be created without one.
    allowNull: true,
  },
  metadata: {
    type: DataTypes.JSONB,
    allowNull: true,
    comment: 'Vertical-specific payload, e.g. {type: "restaurant-reservation", partySize, name, phone}',
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
  indexes: [
    { name: 'idx_bookings_org', fields: ['org_id'] },
    { name: 'idx_bookings_org_start', fields: ['org_id', 'startAt'] },
    { name: 'idx_bookings_user', fields: ['user_id'] },
  ],
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
