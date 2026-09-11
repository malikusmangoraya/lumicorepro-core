import express from 'express';
import { protect } from '../middleware/auth.js';
import Wishlist from '../models/Wishlist.js';
import Product from '../models/Product.js';
import logger from '../utils/logger.js';

const router = express.Router();

/* ══════════════════════════════════════════════════════════════════
 * GET /api/wishlist — list user's wishlist items
 * ══════════════════════════════════════════════════════════════════ */
router.get('/', protect, async (req, res, next) => {
  try {
    const items = await Wishlist.findAll({
      where: { user_id: req.user.id },
      include: [{ model: Product, as: 'product', attributes: ['id', 'title', 'price', 'thumbnail', 'images', 'stock', 'isActive'] }],
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
    const { product_id } = req.body;
    if (!product_id) {
      return res.status(400).json({ success: false, error: 'product_id is required' });
    }

    const product = await Product.findByPk(product_id);
    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    const existing = await Wishlist.findOne({ where: { user_id: req.user.id, product_id } });

    if (existing) {
      await existing.destroy();
      logger.info(`Product ${product_id} removed from wishlist for user ${req.user.id}`);
      return res.json({ success: true, message: 'Removed from wishlist', action: 'removed' });
    }

    const item = await Wishlist.create({ user_id: req.user.id, product_id });
    logger.info(`Product ${product_id} added to wishlist for user ${req.user.id}`);
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
    const item = await Wishlist.findOne({
      where: { user_id: req.user.id, product_id: parseInt(req.params.productId) },
    });

    if (!item) return res.status(404).json({ success: false, error: 'Item not found in wishlist' });

    await item.destroy();
    res.json({ success: true, message: 'Removed from wishlist' });
  } catch (error) {
    next(error);
  }
});

export default router;