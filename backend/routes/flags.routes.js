/**
 * Feature flag routes.
 *
 * GET  /api/flags          — public map of flag key → boolean for the caller
 *                              (resolved against the caller's user id when known)
 * POST /api/flags          — admin upsert { key, enabled, rollout, description }
 */
import express from 'express';
import FeatureFlag from '../models/FeatureFlag.js';
import { protect, authorize } from '../middleware/auth.js';
import { isEnabled } from '../services/featureFlag.service.js';
import { clearFlagCache } from '../services/featureFlag.service.js';

const router = express.Router();

router.get('/', async (req, res, next) => {
  try {
    const userId = req.user?.id ?? null;
    const flags = await FeatureFlag.findAll({ raw: true, attributes: ['key'] });
    const result = {};
    for (const { key } of flags) {
      result[key] = await isEnabled(key, userId);
    }
    res.json({ success: true, data: result });
  } catch (error) {
    next(error);
  }
});

router.post('/', protect, authorize('admin'), async (req, res, next) => {
  try {
    const { key, enabled = false, rollout = 100, description = '' } = req.body || {};
    if (!key || typeof key !== 'string') {
      return res.status(400).json({ success: false, error: 'key is required' });
    }
    const [flag] = await FeatureFlag.upsert(
      { key: key.trim().toLowerCase(), enabled: Boolean(enabled), rollout, description },
      { returning: true }
    );
    clearFlagCache();
    res.json({ success: true, data: flag });
  } catch (error) {
    next(error);
  }
});

export default router;
