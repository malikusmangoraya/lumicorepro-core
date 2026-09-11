import express from 'express';
import { body, validationResult } from 'express-validator';
import { protect, authorize } from '../middleware/auth.js';
import Coupon from '../models/Coupon.js';
import logger from '../utils/logger.js';

const router = express.Router();

/* ══════════════════════════════════════════════════════════════════
 * PUBLIC: Validate coupon code (check if applicable, return discount info)
 * ══════════════════════════════════════════════════════════════════ */
router.post(
  '/validate',
  [body('code').trim().notEmpty().withMessage('Coupon code is required')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { code, subtotal } = req.body;
      const coupon = await Coupon.findOne({
        where: { code: code.toUpperCase(), isActive: true },
      });

      if (!coupon) {
        return res.status(404).json({ success: false, error: 'Coupon not found or inactive' });
      }

      if (coupon.startsAt && new Date(coupon.startsAt) > new Date()) {
        return res.status(400).json({ success: false, error: 'This coupon is not yet active' });
      }

      if (coupon.expiresAt && new Date(coupon.expiresAt) < new Date()) {
        return res.status(400).json({ success: false, error: 'This coupon has expired' });
      }

      if (coupon.usageLimit > 0 && coupon.usageCount >= coupon.usageLimit) {
        return res.status(400).json({ success: false, error: 'This coupon has reached its usage limit' });
      }

      if (subtotal && coupon.minSubtotal > 0 && parseFloat(subtotal) < parseFloat(coupon.minSubtotal)) {
        return res.status(400).json({
          success: false,
          error: `Minimum order subtotal of $${coupon.minSubtotal} required`,
        });
      }

      res.json({
        success: true,
        coupon: {
          code: coupon.code,
          type: coupon.type,
          value: parseFloat(coupon.value),
          maxDiscount: coupon.maxDiscount ? parseFloat(coupon.maxDiscount) : null,
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * ADMIN: CRUD coupons
 * ══════════════════════════════════════════════════════════════════ */
router.get('/', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const page = Math.max(1, parseInt(req.query.page) || 1);
    const limit = Math.min(100, parseInt(req.query.limit) || 20);
    const offset = (page - 1) * limit;

    const { rows, count } = await Coupon.findAndCountAll({
      order: [['createdAt', 'DESC']],
      limit,
      offset,
    });

    res.json({
      success: true,
      data: rows,
      pagination: { page, limit, total: count, pages: Math.ceil(count / limit) },
    });
  } catch (error) {
    next(error);
  }
});

router.post(
  '/',
  protect,
  authorize('admin'),
  [
    body('code').trim().notEmpty().withMessage('Coupon code is required'),
    body('type').isIn(['percentage', 'fixed', 'free_shipping']).withMessage('Invalid coupon type'),
    body('value').isFloat({ min: 0 }).withMessage('Value must be a positive number'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const existing = await Coupon.findOne({ where: { code: req.body.code.toUpperCase() } });
      if (existing) {
        return res.status(400).json({ success: false, error: 'A coupon with this code already exists' });
      }

      const coupon = await Coupon.create({
        ...req.body,
        code: req.body.code.toUpperCase(),
      });

      logger.info(`Coupon created: ${coupon.code}`);
      res.status(201).json({ success: true, data: coupon });
    } catch (error) {
      next(error);
    }
  }
);

router.put(
  '/:id',
  protect,
  authorize('admin'),
  async (req, res, next) => {
    try {
      const coupon = await Coupon.findByPk(req.params.id);
      if (!coupon) return res.status(404).json({ success: false, error: 'Coupon not found' });

      await coupon.update(req.body);
      res.json({ success: true, data: coupon });
    } catch (error) {
      next(error);
    }
  }
);

router.delete('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const coupon = await Coupon.findByPk(req.params.id);
    if (!coupon) return res.status(404).json({ success: false, error: 'Coupon not found' });

    await coupon.destroy();
    res.json({ success: true, message: 'Coupon deleted' });
  } catch (error) {
    next(error);
  }
});

export default router;