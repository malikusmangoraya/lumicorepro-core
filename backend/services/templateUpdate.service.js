/**
 * Sold-template update delivery.
 * --------------------------------
 * publish(product, version, changelog, fileName, adminId)
 *   → marks previous versions stale, inserts the new version, notifies every
 *     buyer (paid order containing the product) via the notifications table
 *     and a live Socket.IO emit to their user room.
 *
 * listForUser(userId)        → updates available for products the user bought.
 * resolveDownload(userId, productId, version?)
 *   → authorizes the requester (must hold a PAID order containing the
 *     product) and returns the file record to stream. Purchase = lifetime
 *     access to that template's updates.
 */
import crypto from 'crypto';
import path from 'path';
import fs from 'fs';
import TemplateVersion from '../models/TemplateVersion.js';
import Order from '../models/Order.js';
import Product from '../models/Product.js';
import Notification from '../models/Notification.js';
import logger from '../utils/logger.js';

export function templateUpdatesDir() {
  return process.env.TEMPLATE_UPDATES_DIR
    || path.join(process.cwd(), 'uploads', 'template-updates');
}

/** Validate a stored file name against the updates dir (traversal-safe). */
export function resolveFilePath(fileName) {
  const root = templateUpdatesDir();
  const resolved = path.resolve(root, path.basename(String(fileName || '')));
  if (!resolved.startsWith(path.resolve(root))) return null;
  return resolved;
}

async function buyerIdsForProduct(productId) {
  // Orders keep items as JSONB: [{product_id, ...}]
  const orders = await Order.findAll({
    where: { isPaid: true },
    attributes: ['user_id', 'items'],
    raw: true,
  });
  const buyers = new Set();
  for (const order of orders) {
    const items = Array.isArray(order.items) ? order.items : [];
    if (items.some((item) => String(item?.product_id) === String(productId)) && order.user_id) {
      buyers.add(order.user_id);
    }
  }
  return [...buyers];
}

export async function publish({ productId, version, changelog = '', fileName, publishedBy = null, productModel = null }) {
  if (!productId || !version) throw Object.assign(new Error('productId and version are required'), { statusCode: 400 });
  if (!/^[0-9]+\.[0-9]+\.[0-9]+$/.test(String(version))) {
    throw Object.assign(new Error('version must be semver (e.g. 1.2.0)'), { statusCode: 400 });
  }

  const ProductModel = productModel || Product;
  const product = await ProductModel.findByPk(productId, { attributes: ['id', 'title'], raw: true });
  if (!product) throw Object.assign(new Error('Product not found'), { statusCode: 404 });

  let file_sha256 = null;
  let file_size_bytes = null;
  if (fileName) {
    const filePath = resolveFilePath(fileName);
    if (!filePath || !fs.existsSync(filePath)) {
      throw Object.assign(new Error(`File not found in ${templateUpdatesDir()}: ${fileName}`), { statusCode: 400 });
    }
    file_size_bytes = fs.statSync(filePath).size;
    file_sha256 = crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
  }

  const published = await TemplateVersion.sequelize.transaction(async (t) => {
    await TemplateVersion.update(
      { is_latest: false },
      { where: { product_id: productId, is_latest: true }, transaction: t },
    );
    return TemplateVersion.create(
      {
        product_id: Number(productId),
        version,
        changelog: String(changelog || '').slice(0, 5000),
        file_name: fileName ? path.basename(fileName) : null,
        file_sha256,
        file_size_bytes,
        published_by: publishedBy ?? null,
        is_latest: true,
      },
      { transaction: t },
    );
  });

  // Notify buyers: durable row + realtime emit.
  const buyers = await buyerIdsForProduct(productId);
  const title = `Update available: ${product.title || 'your template'} v${version}`;
  const message = changelog ? String(changelog).slice(0, 500) : `Version ${version} is ready to download.`;
  const io = global.__lumicore_io || null;
  for (const buyerId of buyers) {
    try {
      await Notification.create({
        recipient: buyerId,
        type: 'system',
        title,
        message,
        link: `/templates/${productId}`,
        metadata: { productId: Number(productId), version, kind: 'template_update' },
      });
      io?.to?.(`user:${buyerId}`)?.emit?.('notification', { title, message, productId, version });
    } catch (err) {
      logger.warn(`Template update notification failed for user ${buyerId}: ${err.message}`);
    }
  }

  return { version: published, buyersNotified: buyers.length };
}

export async function listForUser(userId, productModel = null) {
  const ProductModel = productModel || Product;
  const orders = await Order.findAll({
    where: { user_id: userId, isPaid: true },
    attributes: ['items'],
    raw: true,
  });
  const owned = new Set();
  for (const order of orders) {
    for (const item of Array.isArray(order.items) ? order.items : []) {
      if (item?.product_id != null) owned.add(Number(item.product_id));
    }
  }
  if (owned.size === 0) return [];
  const versions = await TemplateVersion.findAll({
    where: { is_latest: true },
    order: [['created_at', 'DESC']],
    raw: true,
  });
  const ownedArr = [...owned];
  const products = await ProductModel.findAll({
    where: { id: ownedArr },
    attributes: ['id', 'title'],
    raw: true,
  });
  const titles = new Map(products.map((p) => [p.id, p.title]));
  return versions
    .filter((v) => owned.has(Number(v.product_id)))
    .map((v) => ({ ...v, product_title: titles.get(v.product_id) || null }));
}

export async function resolveDownload(userId, productId, version = null) {
  const orders = await Order.findAll({
    where: { user_id: userId, isPaid: true },
    attributes: ['items'],
    raw: true,
  });
  const owns = orders.some((order) =>
    (Array.isArray(order.items) ? order.items : []).some(
      (item) => String(item?.product_id) === String(productId),
    ));
  if (!owns) {
    throw Object.assign(new Error('Purchase required for this download'), { statusCode: 403 });
  }
  const where = version
    ? { product_id: Number(productId), version }
    : { product_id: Number(productId), is_latest: true };
  const record = await TemplateVersion.findOne({ where, raw: true });
  if (!record) throw Object.assign(new Error('Version not found'), { statusCode: 404 });
  const filePath = record.file_name ? resolveFilePath(record.file_name) : null;
  if (!filePath || !fs.existsSync(filePath)) {
    throw Object.assign(new Error('Update package not available'), { statusCode: 404 });
  }
  return { record, filePath };
}

export default { publish, listForUser, resolveDownload, templateUpdatesDir, resolveFilePath };
