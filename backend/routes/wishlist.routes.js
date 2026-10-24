import express from 'express';
import { protect } from '../middleware/auth.js';
import Wishlist from '../models/Wishlist.js';
import Product from '../models/Product.js';
import { tenantWhere } from '../services/tenantScope.service.js';
import logger from '../utils/logger.js';

const router = express.Router();

/** Shared by the lookup here and the join below: a wish can only name a product the caller's tenant can see. */
const productAttributes = ['id', 'title', 'price', 'thumbnail', 'images', 'stock', 'isActive'];

const parseProductId = (value) => {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
};

/* ══════════════════════════════════════════════════════════════════
 * GET /api/wishlist — list user's wishlist items
 * ══════════════════════════════════════════════════════════════════ */
router.get('/', protect, async (req, res, next) => {
  try {
    const items = await Wishlist.findAll({
      where: { user_id: req.user.id },
      include: [
        {
          model: Product,
          as: 'product',
          required: false,
          where: tenantWhere(req),
          attributes: productAttributes,
        },
      ],
      order: [['createdAt', 'DESC']],
    });

    res.json({ success: true, data: items });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * POST /api/wishlist — add product to wishlist (or toggle)
 * ══════════════════════════════════════════════════════════════════ */
router.post('/', protect, async (req, res, next) => {
  try {
    const rawProductId = req.body.product_id;
    if (rawProductId === undefined || rawProductId === null || rawProductId === '') {
      return res.status(400).json({ success: false, error: 'product_id is required' });
    }

    const productId = parseProductId(rawProductId);
    if (productId === null) {
      return res.status(400).json({ success: false, error: 'product_id must be a positive integer' });
    }

    // Tenant-scoped: a bare findByPk let a caller save another org's product.
    const product = await Product.findOne({ where: tenantWhere(req, { id: productId }) });
    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    const existing = await Wishlist.findOne({ where: { user_id: req.user.id, product_id: productId } });

    // Idempotent add. This used to toggle (delete on replay), so a client retry
    // of a failed request silently removed the entry the first call created.
    // Removal is DELETE /api/wishlist/:productId.
    if (existing) {
      return res.json({ success: true, message: 'Already in wishlist', action: 'exists' });
    }

    const item = await Wishlist.create({ user_id: req.user.id, product_id: productId });
    logger.info(`Product ${productId} added to wishlist for user ${req.user.id}`);
    res.status(201).json({ success: true, data: item, action: 'added' });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * DELETE /api/wishlist/:productId — remove product from wishlist
 * ══════════════════════════════════════════════════════════════════ */
router.delete('/:productId', protect, async (req, res, next) => {
  try {
    const productId = parseProductId(req.params.productId);
    if (productId === null) {
      return res.status(404).json({ success: false, error: 'Item not found in wishlist' });
    }

    const item = await Wishlist.findOne({
      where: { user_id: req.user.id, product_id: productId },
    });

    if (!item) return res.status(404).json({ success: false, error: 'Item not found in wishlist' });

    await item.destroy();
    res.json({ success: true, message: 'Removed from wishlist' });
  } catch (error) {
    next(error);
  }
});

export default router;