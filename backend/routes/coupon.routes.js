import express from 'express';
import { body, validationResult } from 'express-validator';
import { protect, optionalProtect, authorize } from '../middleware/auth.js';
import Coupon from '../models/Coupon.js';
import couponService from '../services/couponService.js';
import logger from '../utils/logger.js';

const router = express.Router();

/* ══════════════════════════════════════════════════════════════════
 * PUBLIC: Validate coupon code (check if applicable, return discount info)
 *
 * The rules live in services/couponService.js — this route used to re-implement
 * them inline, which is how the per-user limit and the discount clamps never
 * reached the buyer-facing path.
 * ══════════════════════════════════════════════════════════════════ */
router.post(
  '/validate',
  optionalProtect,
  [
    body('code').trim().notEmpty().withMessage('Coupon code is required'),
    body('subtotal').optional({ values: 'null' }).isFloat({ min: 0 }).withMessage('Subtotal must be a positive number'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { code, subtotal } = req.body;
      const result = await couponService.applyCoupon(code, subtotal ?? null, {
        userId: req.user?.id ?? null,
      });

      if (!result.applied) {
        const status = result.error === 'Coupon not found or inactive' ? 404 : 400;
        return res.status(status).json({ success: false, error: result.error });
      }

      res.json({
        success: true,
        coupon: {
          code: result.coupon.code,
          type: result.coupon.type,
          value: parseFloat(result.coupon.value),
          maxDiscount: result.coupon.maxDiscount ? parseFloat(result.coupon.maxDiscount) : null,
        },
        discount: result.discount,
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * ADMIN: CRUD coupons
 *
 * Admin-only: the `coupons` table has no organization column (codes are
 * platform-wide), so letting a vendor list it exposed every campaign code.
 * ══════════════════════════════════════════════════════════════════ */
const COUPON_FIELDS = [
  'code',
  'type',
  'value',
  'minSubtotal',
  'maxDiscount',
  'usageLimit',
  'perUserLimit',
  'appliesTo',
  'startsAt',
  'expiresAt',
  'isActive',
];

/** `id`, `usageCount` and timestamps are server-owned; a body may not set them. */
const pickCouponFields = (body = {}) => {
  const picked = {};
  for (const key of COUPON_FIELDS) {
    if (body[key] !== undefined) picked[key] = body[key];
  }
  return picked;
};

const parseCouponId = (value) => {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
};

router.get('/', protect, authorize('admin'), async (req, res, next) => {
  try {
    const rawPage = parseInt(req.query.page, 10);
    const rawLimit = parseInt(req.query.limit, 10);
    const page = rawPage > 0 ? rawPage : 1;
    const limit = rawLimit > 0 ? Math.min(100, rawLimit) : 20;
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
        ...pickCouponFields(req.body),
        code: req.body.code.trim().toUpperCase(),
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
  [
    body('code').optional().trim().notEmpty().withMessage('Coupon code cannot be empty'),
    body('type').optional().isIn(['percentage', 'fixed', 'free_shipping']).withMessage('Invalid coupon type'),
    body('value').optional().isFloat({ min: 0 }).withMessage('Value must be a positive number'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const id = parseCouponId(req.params.id);
      if (id === null) return res.status(404).json({ success: false, error: 'Coupon not found' });

      const coupon = await Coupon.findByPk(id);
      if (!coupon) return res.status(404).json({ success: false, error: 'Coupon not found' });

      // Whitelisted: `usageCount` must not be resettable from a request body,
      // and `id`/timestamps are server-owned.
      const updates = pickCouponFields(req.body);
      if (updates.code) updates.code = String(updates.code).trim().toUpperCase();

      await coupon.update(updates);
      res.json({ success: true, data: coupon });
    } catch (error) {
      next(error);
    }
  }
);

router.delete('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const id = parseCouponId(req.params.id);
    if (id === null) return res.status(404).json({ success: false, error: 'Coupon not found' });

    const coupon = await Coupon.findByPk(id);
    if (!coupon) return res.status(404).json({ success: false, error: 'Coupon not found' });

    await coupon.destroy();
    res.json({ success: true, message: 'Coupon deleted' });
  } catch (error) {
    next(error);
  }
});

export default router;