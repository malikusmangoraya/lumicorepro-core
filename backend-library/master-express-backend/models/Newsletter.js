const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/db');

const Newsletter = sequelize.define('Newsletter', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {
      isEmail: true
    }
  },
  name: {
    type: DataTypes.STRING,
    allowNull: true
  },
  isSubscribed: {
    type: DataTypes.BOOLEAN,
    defaultValue: true
  },
  isVerified: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  verificationToken: {
    type: DataTypes.STRING,
    allowNull: true
  },
  lastEmailSent: {
    type: DataTypes.DATE,
    allowNull: true
  }
}, {
  timestamps: true,
  underscored: true
});

module.exports = { Newsletter };
const { sequelize } = require('../config/db');

const Newsletter = sequelize.define('Newsletter', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {
      isEmail: true
    }
  },
  name: {
    type: DataTypes.STRING,
    defaultValue: null
  },
  isSubscribed: {
    type: DataTypes.BOOLEAN,
    defaultValue: true
  },
  subscribeToken: {
    type: DataTypes.STRING,
    defaultValue: null
  },
  isVerified: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  unsubscribedAt: {
    type: DataTypes.DATE,
    defaultValue: null
  }
}, {
  timestamps: true,
  underscored: true,
  indexes: [
    { fields: ['email'] },
    { fields: ['isSubscribed'] },
    { fields: ['isVerified'] }
  ]
});

module.exports = { Newsletter };