/**
 * Privacy routes — GDPR data subject rights.
 *
 * GET    /api/privacy/export   — download everything held about the caller
 * DELETE /api/privacy/account  — erase (anonymize + delete non-essentials)
 */
import express from 'express';
import { protect } from '../middleware/auth.js';
import { exportUserData, eraseUserData } from '../services/privacy.service.js';

const router = express.Router();

router.get('/export', protect, async (req, res, next) => {
  try {
    const data = await exportUserData(req.user.id);
    res.json({ success: true, data });
  } catch (error) {
    next(error);
  }
});

router.delete('/account', protect, async (req, res, next) => {
  try {
    const report = await eraseUserData(req.user.id);
    res.json({ success: true, data: report });
  } catch (error) {
    if (error.statusCode) {
      return res.status(error.statusCode).json({ success: false, error: error.message });
    }
    next(error);
  }
});

export default router;
