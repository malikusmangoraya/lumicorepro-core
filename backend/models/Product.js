import { DataTypes, Model } from 'sequelize';
import { sequelize } from '../config/database.js';

class Product extends Model {}

Product.init(
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    title: {
      type: DataTypes.STRING(255),
      allowNull: false,
      validate: {
        notEmpty: { msg: 'Please provide a product title' },
      },
    },
    slug: {
      type: DataTypes.STRING(255),
      unique: true,
      allowNull: false,
    },
    description: {
      type: DataTypes.TEXT,
      allowNull: false,
    },
    price: {
      type: DataTypes.DECIMAL(10, 2),
      allowNull: false,
      validate: {
        min: { args: [0], msg: 'Price must be non-negative' },
      },
    },
    comparePrice: {
      type: DataTypes.DECIMAL(10, 2),
      defaultValue: 0,
    },
    discountPercentage: {
      type: DataTypes.DECIMAL(5, 2),
      defaultValue: 0,
    },
    sku: {
      type: DataTypes.STRING(100),
      allowNull: true,
    },
    stock: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
      validate: {
        min: { args: [0], msg: 'Stock cannot be negative' },
      },
    },
    category: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },
    tags: {
      type: DataTypes.JSONB,
      defaultValue: [],
    },
    images: {
      type: DataTypes.JSONB,
      defaultValue: [],
    },
    thumbnail: {
      type: DataTypes.STRING(500),
      defaultValue: '',
    },
    rating: {
      type: DataTypes.DECIMAL(3, 2),
      defaultValue: 0,
    },
    reviewCount: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
    },
    attributes: {
      type: DataTypes.JSONB,
      defaultValue: {},
    },
    category_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
vendor_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      comment: 'Product owner (legacy single-tenant)',
    },
    org_id: {
      type: DataTypes.BIGINT.UNSIGNED,
      allowNull: true,
      comment: 'Owning organization (multi-tenant); null = legacy single-tenant',
    },
    isFeatured: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
    },
    isActive: {
      type: DataTypes.BOOLEAN,
      defaultValue: true,
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
    modelName: 'Product',
    tableName: 'products',
    timestamps: true,
    hooks: {
      beforeSave: (product) => {
        if (product.changed('title') || !product.slug) {
          product.slug = product.title
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '') + '-' + Date.now().toString(36);
        }
      },
    },
  }
);

export default Product;
