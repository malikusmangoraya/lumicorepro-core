/**
 * Lemon Squeezy routes.
 * -------------------
 * POST /api/lemonsqueezy/webhook      signed purchase/licence events (no auth)
 * GET  /api/lemonsqueezy/entitlement/:key  public activation check
 * GET  /api/lemonsqueezy/entitlements      admin list
 *
 * The webhook needs the RAW body for HMAC verification, so server.js mounts a
 * raw parser on this path BEFORE express.json().
 */
import express from 'express';
import LicenseEntitlement from '../models/LicenseEntitlement.js';
import {
  verifySignature,
  handleEvent,
  getEntitlement,
  isConfigured,
} from '../services/lemonsqueezy.service.js';
import { protect, authorize } from '../middleware/auth.js';
import { licenseLimiter } from '../middleware/rateLimit.js';
import logger from '../utils/logger.js';

const router = express.Router();

router.post('/webhook', async (req, res) => {
  const raw = Buffer.isBuffer(req.body) ? req.body : Buffer.from(JSON.stringify(req.body ?? {}));
  const signature = req.get('x-signature') || req.get('X-Signature');

  if (!isConfigured()) {
    logger.warn('Lemon Squeezy webhook received but LEMONSQUEEZY_SIGNING_SECRET is not set');
    return res.status(503).json({ success: false, error: 'Webhook not configured' });
  }

  const { verified, reason } = verifySignature(raw, signature);
  if (!verified) {
    logger.warn(`Lemon Squeezy webhook rejected (${reason})`);
    // 401: Lemon Squeezy will retry, but a forged request never gets through.
    return res.status(401).json({ success: false, error: 'Invalid signature' });
  }

  try {
    const outcome = await handleEvent(JSON.parse(raw.toString('utf8')));
    return res.json({ success: true, ...outcome });
  } catch (err) {
    logger.error(`Lemon Squeezy webhook handling failed: ${err.message}`);
    return res.status(500).json({ success: false, error: 'Webhook processing failed' });
  }
});

router.get('/entitlement/:key', licenseLimiter, async (req, res, next) => {
  try {
    const result = await getEntitlement(req.params.key);
    if (!result) return res.status(400).json({ success: false, error: 'key is required' });
    return res.json({ success: true, data: result });
  } catch (err) {
    return next(err);
  }
});

router.get('/entitlements', protect, authorize('admin'), async (req, res, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 50, 200);
    const rows = await LicenseEntitlement.findAll({
      order: [['created_at', 'DESC']],
      limit,
      raw: true,
    });
    return res.json({ success: true, data: rows, configured: isConfigured() });
  } catch (err) {
    return next(err);
  }
});

export default router;