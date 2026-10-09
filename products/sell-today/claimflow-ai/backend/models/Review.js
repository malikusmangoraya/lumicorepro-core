import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Review extends Model {}

Review.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    product_id: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
    user_id: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
    userName: {
      type: DataTypes.STRING(255),
      allowNull: false,
    },
    userAvatar: {
      type: DataTypes.STRING(500),
      defaultValue: '',
    },
    rating: {
      type: DataTypes.INTEGER,
      allowNull: false,
      validate: {
        min: { args: [1], msg: 'Please provide a rating between 1 and 5' },
        max: { args: [5], msg: 'Please provide a rating between 1 and 5' },
      },
    },
    title: {
      type: DataTypes.STRING(100),
      defaultValue: '',
    },
    comment: {
      type: DataTypes.TEXT,
      allowNull: false,
      validate: {
        notEmpty: { msg: 'Please provide a review comment' },
      },
    },
    verifiedPurchase: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    helpfulVotes: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
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
    modelName: 'Review',
    tableName: 'reviews',
    timestamps: true,
    indexes: [
      {
        unique: true,
        fields: ['product_id', 'user_id'],
      },
    ],
  }
);

export default Review;
