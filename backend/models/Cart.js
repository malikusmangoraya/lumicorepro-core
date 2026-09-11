import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Cart extends Model {}

Cart.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    user_id: {
      type: DataTypes.INTEGER,
      allowNull: false,
      unique: true,
    },
    expires_at: {
      type: DataTypes.DATE,
      allowNull: true,
      comment: 'Recovery window deadline — armed when checkout intent is detected',
    },
    abandoned_at: {
      type: DataTypes.DATE,
      allowNull: true,
      comment: 'Set by the cart-recovery worker once the recovery email fires',
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
    modelName: 'Cart',
    tableName: 'carts',
    timestamps: true,
  }
);

export default Cart;