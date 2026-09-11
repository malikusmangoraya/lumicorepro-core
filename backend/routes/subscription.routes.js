import express from 'express';
import { body, validationResult } from 'express-validator';
import { protect, authorize } from '../middleware/auth.js';
import Subscription from '../models/Subscription.js';
import User from '../models/User.js';
import Plan from '../models/Plan.js';
import stripeService from '../services/payment/stripe.service.js';
import logger from '../utils/logger.js';

const router = express.Router();

/* ══════════════════════════════════════════════════════════════════
 * GET /api/subscriptions — list user's subscriptions (with plan data)
 * ══════════════════════════════════════════════════════════════════ */
router.get('/', protect, async (req, res, next) => {
  try {
    const subs = await Subscription.findAll({
      where: { user_id: req.user.id },
      order: [['createdAt', 'DESC']],
      include: [{ model: Plan, as: 'plan', attributes: ['id', 'name', 'slug', 'amount', 'currency', 'interval', 'features'] }],
    });

    res.json({ success: true, data: subs });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * POST /api/subscriptions — create a subscription via Stripe Checkout
 * Body: { planId } → returns checkout URL
 * ══════════════════════════════════════════════════════════════════ */
router.post(
  '/',
  protect,
  [body('planId').isInt().withMessage('Valid planId is required')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const plan = await Plan.findByPk(req.body.planId);
      if (!plan || !plan.isActive) {
        return res.status(404).json({ success: false, error: 'Plan not found' });
      }
      if (plan.interval === 'one_time') {
        return res.status(400).json({ success: false, error: 'Use /payments/checkout for one-time credit packs' });
      }

      const baseUrl = (process.env.FRONTEND_URL || 'http://localhost:5173').replace(/\/+$/, '');
      const session = await stripeService.createCheckoutSession({
        user: req.user,
        priceId: plan.stripePriceId,
        mode: 'subscription',
        successUrl: `${baseUrl}/billing?success=1`,
        cancelUrl: `${baseUrl}/pricing?canceled=1`,
        metadata: { planId: plan.slug, subscription: '1' },
        credits: parseFloat(plan.creditsGrant || 0),
      });

      if (session.customerId && !req.user.stripeCustomerId) {
        await User.update({ stripeCustomerId: session.customerId }, { where: { id: req.user.id } });
      }

      logger.info(`Subscription checkout created for user ${req.user.id}: ${plan.slug}`);
      res.status(201).json({ success: true, checkoutUrl: session.url, sessionId: session.id, plan: plan.slug });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * PATCH /api/subscriptions/:id/cancel — cancel at Stripe
 * ══════════════════════════════════════════════════════════════════ */
router.patch('/:id/cancel', protect, async (req, res, next) => {
  try {
    const sub = await Subscription.findOne({
      where: { id: parseInt(req.params.id), user_id: req.user.id },
    });

    if (!sub) return res.status(404).json({ success: false, error: 'Subscription not found' });
    if (sub.status === 'canceled' || sub.status === 'cancelled') {
      return res.status(400).json({ success: false, error: 'Subscription is already cancelled' });
    }

    if (sub.stripeSubscriptionId) {
      try {
        await stripeService.cancelSubscription(sub.stripeSubscriptionId);
      } catch (stripeErr) {
        logger.warn(`Stripe cancel failed for ${sub.stripeSubscriptionId}: ${stripeErr.message}`);
      }
    }

    await sub.update({ status: 'canceled', cancelAtPeriodEnd: false });
    logger.info(`Subscription ${sub.id} cancelled for user ${req.user.id}`);
    res.json({ success: true, data: sub });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * DELETE /api/subscriptions/:id — remove local record only
 * ══════════════════════════════════════════════════════════════════ */
router.delete('/:id', protect, async (req, res, next) => {
  try {
    const sub = await Subscription.findOne({
      where: { id: parseInt(req.params.id), user_id: req.user.id },
    });

    if (!sub) return res.status(404).json({ success: false, error: 'Subscription not found' });

    await sub.destroy();
    res.json({ success: true, message: 'Subscription removed' });
  } catch (error) {
    next(error);
  }
});

export default router;