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
  body('is_default').optional().isBoolean().withMessage('is_default must be a boolean'),
];

// The same rules, but every field is optional: PUT is a partial update.
const addressUpdateValidation = [
  body('name').optional().trim().notEmpty().withMessage('Name cannot be empty'),
  body('address_line1').optional().trim().notEmpty().withMessage('Street address cannot be empty'),
  body('city').optional().trim().notEmpty().withMessage('City cannot be empty'),
  body('country').optional().trim().notEmpty(),
  body('label').optional().isIn(['shipping', 'billing']).withMessage('Invalid address label'),
  body('is_default').optional().isBoolean().withMessage('is_default must be a boolean'),
];

/**
 * Columns a client may write. `user_id`, `id` and the timestamps are
 * server-owned: spreading the raw body let a caller re-parent an address to
 * another account (POST) or rewrite its owner (PUT).
 */
const ADDRESS_FIELDS = [
  'name',
  'phone',
  'address_line1',
  'address_line2',
  'city',
  'state',
  'postal_code',
  'country',
  'label',
];

const pickAddressFields = (body = {}) => {
  const picked = {};
  for (const key of ADDRESS_FIELDS) {
    if (body[key] !== undefined) picked[key] = body[key];
  }
  return picked;
};

/** Non-numeric ids would reach SQL as NaN and abort the query on PostgreSQL. */
const parseAddressId = (value) => {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
};

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
      ...pickAddressFields(req.body),
      user_id: req.user.id,
      is_default: req.body.is_default === true,
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
router.put('/:id', protect, addressUpdateValidation, async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ success: false, errors: errors.array() });
    }

    const id = parseAddressId(req.params.id);
    if (id === null) return res.status(404).json({ success: false, error: 'Address not found' });

    const address = await Address.findOne({
      where: { id, user_id: req.user.id },
    });

    if (!address) return res.status(404).json({ success: false, error: 'Address not found' });

    if (req.body.is_default === true) {
      await Address.update({ is_default: false }, { where: { user_id: req.user.id } });
    }

    // Whitelisted, so `user_id`/`id` in the body cannot re-parent the row.
    const updates = pickAddressFields(req.body);
    if (req.body.is_default !== undefined) {
      updates.is_default = req.body.is_default === true;
    }

    await address.update(updates);
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
    const id = parseAddressId(req.params.id);
    if (id === null) return res.status(404).json({ success: false, error: 'Address not found' });

    const address = await Address.findOne({
      where: { id, user_id: req.user.id },
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
    const id = parseAddressId(req.params.id);
    if (id === null) return res.status(404).json({ success: false, error: 'Address not found' });

    const address = await Address.findOne({
      where: { id, user_id: req.user.id },
    });

    if (!address) return res.status(404).json({ success: false, error: 'Address not found' });

    await address.destroy();
    res.json({ success: true, message: 'Address deleted' });
  } catch (error) {
    next(error);
  }
});

export default router;