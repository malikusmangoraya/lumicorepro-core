import express from 'express';
import { protect, authorize } from '../middleware/auth.js';
import Plan from '../models/Plan.js';
import logger from '../utils/logger.js';

const router = express.Router();

/**
 * GET /api/plans — list active pricing plans / credit packs
 */
router.get('/', async (req, res, next) => {
  try {
    const plans = await Plan.findAll({
      where: { isActive: true },
      order: [['sortOrder', 'ASC']],
    });
    res.json({ success: true, data: plans });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/plans — create a plan (Admin only)
 */
router.post('/', protect, authorize('admin'), async (req, res, next) => {
  try {
    const plan = await Plan.create(req.body);
    logger.info(`Plan created: ${plan.slug}`);
    res.status(201).json({ success: true, data: plan });
  } catch (error) {
    next(error);
  }
});

/**
 * PATCH /api/plans/:id — update a plan (Admin only)
 */
router.patch('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const plan = await Plan.findByPk(req.params.id);
    if (!plan) return res.status(404).json({ success: false, error: 'Plan not found' });
    await plan.update(req.body);
    res.json({ success: true, data: plan });
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/plans/:id — soft-deactivate a plan (Admin only)
 */
router.delete('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const plan = await Plan.findByPk(req.params.id);
    if (!plan) return res.status(404).json({ success: false, error: 'Plan not found' });
    await plan.update({ isActive: false });
    res.json({ success: true, message: 'Plan deactivated' });
  } catch (error) {
    next(error);
  }
});

export default router;