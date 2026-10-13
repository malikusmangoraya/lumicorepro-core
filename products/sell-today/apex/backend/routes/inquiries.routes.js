import express from 'express';
import inquiryService from '../services/inquiry.service.js';
import { protect, optionalProtect, adminOnly } from '../middleware/auth.js';
import { recordAudit } from '../middleware/audit.js';
import { inquiryLimiter } from '../middleware/rateLimit.js';
import logger from '../utils/logger.js';

/**
 * Enquiry routes — mounted by `server.js` at /api/inquiries.
 *
 *   POST   /            public (rate limited). Anonymous is allowed, but an
 *                       authenticated caller is bound to their own account.
 *   GET    /mine        authenticated; returns the caller's enquiries only.
 *   GET    /admin       admin only; the staff lead queue.
 *   PATCH  /:id/status  admin only; advances the lead.
 *
 * `user_id` is taken from the session, never from the body, so the ownership
 * boundary cannot be widened by a crafted payload.
 */
const router = express.Router();

const now = () => new Date().toISOString();

function sendError(res, err, fallbackMessage) {
  const status = err?.status;

  if (status === 400 || err?.name === 'InquiryValidationError') {
    return res.status(400).json({
      success: false,
      status: 400,
      message: err?.message || 'Invalid enquiry',
      errors: err?.errors || [],
      timestamp: now(),
    });
  }

  if (status === 404 || err?.name === 'InquiryNotFoundError') {
    return res.status(404).json({
      success: false,
      status: 404,
      message: 'Enquiry not found',
      timestamp: now(),
    });
  }

  logger.error(`[inquiries] ${fallbackMessage}: ${err?.message}`);
  return res.status(500).json({
    success: false,
    status: 500,
    message: fallbackMessage,
    timestamp: now(),
  });
}

/* ── Public: submit an enquiry ───────────────────────────────────────────── */

router.post('/', inquiryLimiter, optionalProtect, async (req, res) => {
  try {
    const { inquiry, created } = await inquiryService.createInquiry(req.body, {
      userId: req.user?.id ?? null,
    });

    if (created) {
      recordAudit(req, {
        action: 'inquiry.create',
        userId: req.user?.id ?? null,
        email: inquiry.email,
        meta: { inquiryId: inquiry.id, vehicleId: inquiry.vehicle_id ?? null },
      });
    }

    res.status(created ? 201 : 200).json({
      success: true,
      status: created ? 201 : 200,
      message: created ? 'Enquiry received' : 'Enquiry already received',
      data: inquiry,
      timestamp: now(),
    });
  } catch (err) {
    sendError(res, err, 'Could not submit your enquiry');
  }
});

/* ── Buyer: my enquiries ─────────────────────────────────────────────────── */

router.get('/mine', protect, async (req, res) => {
  try {
    const result = await inquiryService.listOwnInquiries(req.user?.id, req.query);
    res.json({ success: true, status: 200, message: 'Enquiries listed', data: result, timestamp: now() });
  } catch (err) {
    sendError(res, err, 'Could not load your enquiries');
  }
});

/* ── Staff: the lead queue ───────────────────────────────────────────────── */

router.get('/admin', protect, adminOnly, async (req, res) => {
  try {
    const result = await inquiryService.listAdminInquiries(req.query);
    res.json({ success: true, status: 200, message: 'Enquiries listed', data: result, timestamp: now() });
  } catch (err) {
    sendError(res, err, 'Could not load enquiries');
  }
});

router.patch('/:id/status', protect, adminOnly, async (req, res) => {
  try {
    const inquiry = await inquiryService.updateInquiryStatus(req.params.id, req.body?.status);
    recordAudit(req, {
      action: 'inquiry.status.change',
      userId: req.user?.id ?? null,
      email: req.user?.email ?? null,
      meta: { inquiryId: inquiry.id, status: inquiry.status },
    });
    res.json({ success: true, status: 200, message: 'Enquiry updated', data: inquiry, timestamp: now() });
  } catch (err) {
    sendError(res, err, 'Could not update the enquiry');
  }
});

export default router;
