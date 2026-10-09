/**
 * License API (self-hosted, free)
 * --------------------------------
 * POST /api/license/validate  — validate a license key (public, rate-limited)
 * POST /api/license/issue     — admin-only: mint full/trial keys
 * GET  /api/license/metadata  — product code + trial length (public)
 *
 * No external licensing SaaS. Secrets live in .env only.
 */
import express from 'express';
import {
  generateLicenseKey,
  generateTrialKey,
  validateLicenseKey,
  groupCode,
} from '../utils/license.js';
import { protect, authorize } from '../middleware/auth.js';
import { licenseLimiter } from '../middleware/rateLimit.js';
import response from '../utils/response.js';
import logger from '../utils/logger.js';

const router = express.Router();

/**
 * @swagger
 * /api/license/validate:
 *   post:
 *     summary: Validate a license key (trial or full)
 *     tags: [License]
 */
router.post('/validate', licenseLimiter, (req, res) => {
  const key = (req.body && req.body.key) || '';
  if (!key || typeof key !== 'string') {
    return response.sendValidationError(res, [{ field: 'key', error: 'License key is required' }]);
  }
  const result = validateLicenseKey(key);
  if (result.status === 'unconfigured') {
    logger.warn('LICENSE_SECRET missing — license validation not configured');
    return response.sendServerError(res, 'License validation is not configured yet', null);
  }
  return response.sendSuccess(res, {
    valid: result.valid,
    status: result.status,
    licenseType: result.licenseType,
    trial: result.trial,
    daysLeft: result.daysLeft,
    product: result.product,
    features: result.features || [],
  });
});

/**
 * @swagger
 * /api/license/issue:
 *   post:
 *     summary: Mint a new license key (admin only)
 *     tags: [License]
 */
router.post('/issue', protect, authorize('admin'), (req, res) => {
  const { licenseType = 'full', days = 0, features = [] } = req.body || {};
  try {
    if (licenseType === 'trial') {
      const t = generateTrialKey();
      return response.sendSuccess(
        res,
        { key: t.key, licenseType: 'trial', expiry: t.expiry },
        null,
        201
      );
    }
    const k = generateLicenseKey({ licenseType, days: Number(days) || 0, features });
    return response.sendSuccess(res, { key: k.key, licenseType, expiry: k.expiry }, null, 201);
  } catch (error) {
    logger.error(`License issue failed: ${error.message}`);
    return response.sendServerError(res, 'License generation failed', null);
  }
});

/**
 * @swagger
 * /api/license/metadata:
 *   get:
 *     summary: Product code + trial length (public, non-sensitive)
 *     tags: [License]
 */
router.get('/metadata', (req, res) => {
  return response.sendSuccess(res, {
    product: process.env.LICENSE_PRODUCT || 'lumicorepro-core',
    trialDays: parseInt(process.env.LICENSE_TRIAL_DAYS || '14', 10),
    trialWatermark: true,
  });
});

export default router;
