/**
 * LumicorePro — Server-Side Cart Routes
 * Provides persistent cart storage in PostgreSQL via Cart + CartItem models.
 * Each authenticated user has exactly one cart (created on first access).
 */
import express from 'express';
import { body, validationResult } from 'express-validator';
import Cart from '../models/Cart.js';
import CartItem from '../models/CartItem.js';
import Product from '../models/Product.js';
import { protect } from '../middleware/auth.js';
import { armCartRecovery, disarmCartRecovery } from '../services/checkout/recovery.service.js';
import logger from '../utils/logger.js';

const router = express.Router();

// All cart routes require authentication
router.use(protect);

/**
 * Helper — get or lazily create the user's cart
 */
async function getOrCreateCart(userId) {
  const [cart] = await Cart.findOrCreate({
    where: { user_id: userId },
    defaults: { user_id: userId },
  });
  return cart;
}

/**
 * GET /api/cart
 * Return the authenticated user's cart with all items and product details.
 */
router.get('/', async (req, res, next) => {
  try {
    const cart = await getOrCreateCart(req.user.id);

    const items = await CartItem.findAll({
      where: { cart_id: cart.id },
      include: [
        {
          model: Product,
          as: 'product',
          attributes: [
            'id',
            'title',
            'slug',
            'price',
            'comparePrice',
            'thumbnail',
            'stock',
            'isActive',
          ],
          required: false,
        },
      ],
      order: [['createdAt', 'ASC']],
    });

    const subtotal = items.reduce(
      (sum, item) => sum + parseFloat(item.price || 0) * item.quantity,
      0
    );

    res.json({
      success: true,
      data: {
        cartId: cart.id,
        items,
        subtotal: Math.round(subtotal * 100) / 100,
        count: items.reduce((sum, item) => sum + item.quantity, 0),
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/cart/items
 * Add a product to cart or increment its quantity if already present.
 */
router.post(
  '/items',
  [
    body('productId').isInt({ min: 1 }).withMessage('Valid product ID is required'),
    body('quantity').optional().isInt({ min: 1, max: 100 }).withMessage('Quantity must be 1–100'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { productId, quantity = 1, selectedColor, selectedSize } = req.body;

      // Validate product exists and has stock
      const product = await Product.findByPk(productId);
      if (!product || !product.isActive) {
        return res.status(404).json({ success: false, error: 'Product not found or unavailable' });
      }
      if (product.stock < quantity) {
        return res.status(400).json({
          success: false,
          error: `Only ${product.stock} unit(s) in stock`,
        });
      }

      const cart = await getOrCreateCart(req.user.id);

      // Check if item already in cart
      const existing = await CartItem.findOne({
        where: {
          cart_id: cart.id,
          product_id: productId,
          ...(selectedColor ? { selectedColor } : {}),
          ...(selectedSize ? { selectedSize } : {}),
        },
      });

      let item;
      if (existing) {
        const newQty = existing.quantity + quantity;
        if (product.stock < newQty) {
          return res.status(400).json({
            success: false,
            error: `Cannot add ${quantity} more — only ${product.stock - existing.quantity} unit(s) available`,
          });
        }
        await existing.update({ quantity: newQty });
        item = existing;
      } else {
        item = await CartItem.create({
          cart_id: cart.id,
          product_id: productId,
          quantity,
          price: parseFloat(product.price),
          title: product.title,
          thumbnail: product.thumbnail || '',
          selectedColor: selectedColor || null,
          selectedSize: selectedSize || null,
        });
      }

      logger.info(`Cart item added: product ${productId} x${quantity} for user ${req.user.id}`);
      await armCartRecovery(cart).catch(() => {});

      res.status(201).json({ success: true, data: item });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * PUT /api/cart/items/:itemId
 * Update the quantity of a specific cart item.
 */
router.put(
  '/items/:itemId',
  [body('quantity').isInt({ min: 0, max: 100 }).withMessage('Quantity must be 0–100')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const cart = await getOrCreateCart(req.user.id);
      const item = await CartItem.findOne({
        where: { id: req.params.itemId, cart_id: cart.id },
      });

      if (!item) {
        return res.status(404).json({ success: false, error: 'Cart item not found' });
      }

      const { quantity } = req.body;

      if (quantity === 0) {
        // Treat quantity=0 as remove
        await item.destroy();
        await disarmCartRecovery(req.user.id).catch(() => {});
        return res.json({ success: true, message: 'Item removed from cart', removed: true });
      }

      // Validate stock
      const product = await Product.findByPk(item.product_id);
      if (product && product.stock < quantity) {
        return res.status(400).json({
          success: false,
          error: `Only ${product.stock} unit(s) in stock`,
        });
      }

      await item.update({ quantity });
      await armCartRecovery(cart).catch(() => {});
      res.json({ success: true, data: item });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * DELETE /api/cart/items/:itemId
 * Remove a specific item from the cart.
 */
router.delete('/items/:itemId', async (req, res, next) => {
  try {
    const cart = await getOrCreateCart(req.user.id);
    const item = await CartItem.findOne({
      where: { id: req.params.itemId, cart_id: cart.id },
    });

    if (!item) {
      return res.status(404).json({ success: false, error: 'Cart item not found' });
    }

    await item.destroy();
    await disarmCartRecovery(req.user.id).catch(() => {});
    res.json({ success: true, message: 'Item removed from cart' });
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/cart
 * Clear all items from the user's cart.
 */
router.delete('/', async (req, res, next) => {
  try {
    const cart = await getOrCreateCart(req.user.id);
    await CartItem.destroy({ where: { cart_id: cart.id } });
    await disarmCartRecovery(req.user.id).catch(() => {});
    res.json({ success: true, message: 'Cart cleared successfully' });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/cart/count
 * Lightweight endpoint — just returns total item count (for nav badge).
 */
router.get('/count', async (req, res, next) => {
  try {
    const cart = await Cart.findOne({ where: { user_id: req.user.id } });
    if (!cart) return res.json({ success: true, count: 0 });

    const items = await CartItem.findAll({ where: { cart_id: cart.id }, attributes: ['quantity'] });
    const count = items.reduce((sum, item) => sum + item.quantity, 0);
    res.json({ success: true, count });
  } catch (error) {
    next(error);
  }
});

export default router;
