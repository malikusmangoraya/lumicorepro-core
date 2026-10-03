import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';
import bcrypt from 'bcryptjs';

class User extends Model {}

User.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    name: {
      type: DataTypes.STRING(255),
      allowNull: false,
      validate: {
        notEmpty: { msg: 'Please provide a name' },
      },
    },
    email: {
      type: DataTypes.STRING(255),
      allowNull: false,
      unique: true,
      validate: {
        isEmail: { msg: 'Please provide a valid email' },
      },
    },
    password: {
      type: DataTypes.STRING(255),
      allowNull: false,
    },
    role: {
      type: DataTypes.STRING(50),
      defaultValue: 'user',
      validate: {
        isIn: { args: [['user', 'admin', 'vendor']], msg: 'Invalid role' },
      },
    },
    avatar: {
      type: DataTypes.STRING(500),
      defaultValue: '',
    },
    phone: {
      type: DataTypes.STRING(50),
      defaultValue: '',
    },
    stripeCustomerId: {
      type: DataTypes.STRING(255),
      allowNull: true,
      comment: 'Stripe Customer ID for subscriptions + one-time payments',
    },
    isVerified: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    isActive: {
      type: DataTypes.BOOLEAN,
      defaultValue: true,
    },
    betaStatus: {
      type: DataTypes.ENUM('active', 'waitlist', 'denied'),
      defaultValue: 'active',
      comment: 'Waitlist gate: "waitlist" users can log in but cannot generate until approved.',
    },
    verificationToken: {
      type: DataTypes.STRING(255),
      allowNull: true,
      comment: 'One-time email-verification token (cleared after verification)',
    },
    verificationExpires: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    resetPasswordToken: {
      type: DataTypes.STRING(255),
      allowNull: true,
      comment: 'One-time password-reset token (cleared after use/expiry)',
    },
    resetPasswordExpires: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    twoFactorEnabled: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    twoFactorMethod: {
      type: DataTypes.STRING(50),
      allowNull: true,
      defaultValue: 'email',
    },
    twoFactorSecret: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    twoFactorActivatedAt: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    oauthProvider: {
      type: DataTypes.STRING(50),
      allowNull: true,
      comment: 'google | facebook | github — set when account logged in via OAuth',
    },
    oauthId: {
      type: DataTypes.STRING(255),
      allowNull: true,
    },
    current_org_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      comment: 'Active organization for the session (multi-tenant)',
    },
    lastLogin: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    preferences: {
      type: DataTypes.JSONB,
      defaultValue: {
        theme: 'light',
        language: 'en',
        notifications: { email: true, push: true },
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
    modelName: 'User',
    tableName: 'users',
    timestamps: true,
    hooks: {
      beforeSave: async (user) => {
        if (user.changed('password')) {
          const salt = await bcrypt.genSalt(12);
          user.password = await bcrypt.hash(user.password, salt);
        }
      },
    },
    defaultScope: {
      attributes: {
        exclude: [
          'password',
          'verificationToken',
          'verificationExpires',
          'resetPasswordToken',
          'resetPasswordExpires',
        ],
      },
    },
    scopes: {
      withPassword: {
        attributes: {},
      },
    },
  }
);

User.prototype.comparePassword = async function (candidatePassword) {
  return bcrypt.compare(candidatePassword, this.password);
};

export default User;
