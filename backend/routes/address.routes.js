import express from 'express';
import { body, validationResult } from 'express-validator';
import { protect } from '../middleware/auth.js';
import Address from '../models/Address.js';
import logger from '../utils/logger.js';

const router = express.Router();

const addressValidation = [
  body('name').trim().notEmpty().withMessage('Name is required'),
  body('address_line1').trim().notEmpty().withMessage('Street address is required'),
  body('city').trim().notEmpty().withMessage('City is required'),
  body('country').optional().trim().notEmpty(),
  body('label').optional().isIn(['shipping', 'billing']).withMessage('Invalid address label'),
];

/* ══════════════════════════════════════════════════════════════════
 * GET /api/addresses — list user's addresses
 * ══════════════════════════════════════════════════════════════════ */
router.get('/', protect, async (req, res, next) => {
  try {
    const addresses = await Address.findAll({
      where: { user_id: req.user.id },
      order: [['is_default', 'DESC'], ['createdAt', 'DESC']],
    });

    res.json({ success: true, data: addresses });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * POST /api/addresses — create address (optionally set as default)
 * ══════════════════════════════════════════════════════════════════ */
router.post('/', protect, addressValidation, async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ success: false, errors: errors.array() });
    }

    const data = {
      user_id: req.user.id,
      ...req.body,
      is_default: req.body.is_default ?? false,
    };

    if (data.is_default) {
      await Address.update({ is_default: false }, { where: { user_id: req.user.id } });
    }

    const address = await Address.create(data);
    logger.info(`Address created for user ${req.user.id}`);
    res.status(201).json({ success: true, data: address });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * PUT /api/addresses/:id — update address
 * ══════════════════════════════════════════════════════════════════ */
router.put('/:id', protect, async (req, res, next) => {
  try {
    const address = await Address.findOne({
      where: { id: parseInt(req.params.id), user_id: req.user.id },
    });

    if (!address) return res.status(404).json({ success: false, error: 'Address not found' });

    if (req.body.is_default) {
      await Address.update({ is_default: false }, { where: { user_id: req.user.id } });
    }

    await address.update(req.body);
    res.json({ success: true, data: address });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * PATCH /api/addresses/:id/default — set as default
 * ══════════════════════════════════════════════════════════════════ */
router.patch('/:id/default', protect, async (req, res, next) => {
  try {
    const address = await Address.findOne({
      where: { id: parseInt(req.params.id), user_id: req.user.id },
    });

    if (!address) return res.status(404).json({ success: false, error: 'Address not found' });

    await Address.update({ is_default: false }, { where: { user_id: req.user.id } });
    await address.update({ is_default: true });

    res.json({ success: true, data: address });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * DELETE /api/addresses/:id — delete address
 * ══════════════════════════════════════════════════════════════════ */
router.delete('/:id', protect, async (req, res, next) => {
  try {
    const address = await Address.findOne({
      where: { id: parseInt(req.params.id), user_id: req.user.id },
    });

    if (!address) return res.status(404).json({ success: false, error: 'Address not found' });

    await address.destroy();
    res.json({ success: true, message: 'Address deleted' });
  } catch (error) {
    next(error);
  }
});

export default router;