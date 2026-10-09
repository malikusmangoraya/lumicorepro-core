import { DataTypes } from 'sequelize';
import { sequelize } from '../config/database.js';

/**
 * TemplateVersion — a published update for a sold template/product.
 *
 * The marketplace previously had no mechanism to deliver template updates to
 * buyers after purchase. Admins publish a version (semver + changelog + file
 * under TEMPLATE_UPDATES_DIR); every buyer (paid order containing the product)
 * is notified and can download the latest version.
 */
const TemplateVersion = sequelize.define(
  'TemplateVersion',
  {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    product_id: { type: DataTypes.INTEGER, allowNull: false },
    version: { type: DataTypes.STRING(32), allowNull: false },
    changelog: { type: DataTypes.TEXT, allowNull: true },
    // File NAME (not path) resolved against TEMPLATE_UPDATES_DIR — path
    // traversal is impossible by construction.
    file_name: { type: DataTypes.STRING(255), allowNull: true },
    file_sha256: { type: DataTypes.STRING(64), allowNull: true },
    file_size_bytes: { type: DataTypes.INTEGER, allowNull: true },
    published_by: { type: DataTypes.INTEGER, allowNull: true },
    is_latest: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: true },
    created_at: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW },
  },
  {
    tableName: 'template_versions',
    timestamps: false,
    updatedAt: false,
    indexes: [
      { unique: true, fields: ['product_id', 'version'] },
      { fields: ['product_id', 'is_latest'] },
    ],
  },
);

export default TemplateVersion;
