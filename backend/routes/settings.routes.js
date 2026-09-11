import express from 'express';
import bcrypt from 'bcryptjs';
import systemConfig from '../services/systemConfig.service.js';
import User from '../models/User.js';
import { protect, authorize, generateToken } from '../middleware/auth.js';
import logger from '../utils/logger.js';
import { CURRENCY_LIST } from '../config/currency.js';
import stripeService from '../services/payment/stripe.service.js';
import paypalService from '../services/payment/paypal.service.js';

const router = express.Router();

const SANITIZE_REGEX = /^[a-zA-Z0-9._+\- ]+$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const invalid = (res, msg, code = 'INVALID_INPUT') =>
  res.status(422).json({ success: false, error: msg, code });

const pickString = (obj, key, maxLen = 255) => {
  const val = obj?.[key];
  return typeof val === 'string' ? val.trim().slice(0, maxLen) : '';
};

/**
 * GET /api/settings/status — public
 * Used by the frontend SetupGate to decide whether to redirect new deployments
 * to /setup. Fails open (configured=true) when the DB is unavailable so demo
 * and offline flows are never locked out.
 */
router.get('/status', async (req, res) => {
  try {
    const configured = await systemConfig.isConfigured();
    res.json({ success: true, data: { configured, needsSetup: !configured } });
  } catch (err) {
    logger.warn(`settings/status failed: ${err.message}`);
    res.json({ success: true, data: { configured: true, needsSetup: false } });
  }
});

/**
 * GET /api/settings/public — public
 * Masked snapshot (never exposes secrets). Consumed by checkout UI,
 * branding components and the payment /config endpoint.
 */
router.get('/public', async (req, res) => {
  try {
    const config = await systemConfig.getPublicConfig();
    res.json({ success: true, data: config });
  } catch (err) {
    res.status(500).json({ success: false, error: 'Unable to load system settings' });
  }
});

/**
 * GET /api/settings/system — admin only
 * Full safe snapshot for the Admin Settings panel (secrets masked).
 */
router.get('/system', protect, authorize('admin'), async (req, res) => {
  try {
    const config = await systemConfig.getAll();
    res.json({ success: true, data: systemConfig.maskAdminConfig(config) });
  } catch (err) {
    res.status(500).json({ success: false, error: 'Unable to load system settings' });
  }
});

/**
 * PUT /api/settings/system — admin only
 * No-code "Global System Settings" save. Validates every submitted group and
 * persists it to the SystemConfig table (cache refreshed automatically).
 */
router.put('/system', protect, authorize('admin'), async (req, res) => {
  try {
    const { business, currency, payments, smtp } = req.body || {};

    const updates = {};

    // ── business ──────────────────────────────────────────────
    if (business !== undefined) {
      if (typeof business !== 'object') return invalid(res, 'business must be an object');
      const name = pickString(business, 'name', 80);
      if (!name) return invalid(res, 'Business name is required');
      updates.business = {
        name,
        tagline: pickString(business, 'tagline', 140),
        logoUrl: pickString(business, 'logoUrl', 500),
        supportEmail: pickString(business, 'supportEmail', 120),
      };
      if (updates.business.supportEmail && !EMAIL_REGEX.test(updates.business.supportEmail)) {
        return invalid(res, 'Support email is not valid', 'INVALID_EMAIL');
      }
    }

    // ── currency ──────────────────────────────────────────────
    if (currency !== undefined) {
      if (typeof currency !== 'object') return invalid(res, 'currency must be an object');
      const code = pickString(currency, 'code', 3).toUpperCase();
      if (!CURRENCY_LIST[code]) {
        return invalid(res, `Unsupported currency: ${code || '(empty)'}`, 'INVALID_CURRENCY');
      }
      updates.currency = { code, symbol: CURRENCY_LIST[code].symbol };
    }

    // ── payments ──────────────────────────────────────────────
    if (payments !== undefined && typeof payments === 'object') {
      const params = {};

      if (payments.stripe !== undefined && typeof payments.stripe === 'object') {
        const s = payments.stripe;
        const mode = s.mode === 'live' ? 'live' : 'sandbox';
        const secretKey = pickString(s, 'secretKey', 200);
        const publishableKey = pickString(s, 'publishableKey', 200);
        const webhookSecret = pickString(s, 'webhookSecret', 200);
        params.stripe = {
          enabled: Boolean(secretKey && publishableKey && !secretKey.includes('your_')),
          mode,
          secretKey,
          publishableKey,
          webhookSecret,
        };
      }

      if (payments.paypal !== undefined && typeof payments.paypal === 'object') {
        const p = payments.paypal;
        const clientId = pickString(p, 'clientId', 160);
        const clientSecret = pickString(p, 'clientSecret', 200);
        params.paypal = {
          enabled: Boolean(clientId && clientSecret && !clientId.includes('your_')),
          mode: p.mode === 'live' ? 'live' : 'sandbox',
          clientId,
          clientSecret,
          webhookId: pickString(p, 'webhookId', 200),
        };
      }

      if (Object.keys(params).length) updates.payments = params;
    }

    // ── smtp ──────────────────────────────────────────────────
    if (smtp !== undefined && typeof smtp === 'object') {
      const host = pickString(smtp, 'host', 200);
      const user = pickString(smtp, 'user', 200);
      const pass = pickString(smtp, 'pass', 200);
      const port = Number(smtp.port);
      updates.smtp = {
        enabled: Boolean(host && user && pass),
        host,
        port: port > 0 && port < 65536 ? port : 587,
        secure: Boolean(smtp.secure) || port === 465,
        user,
        pass,
        fromName: pickString(smtp, 'fromName', 120),
        fromEmail: pickString(smtp, 'fromEmail', 120),
      };
      if (updates.smtp.fromEmail && !EMAIL_REGEX.test(updates.smtp.fromEmail)) {
        return invalid(res, 'From email is not valid', 'INVALID_EMAIL');
      }
    }

    await systemConfig.bulkSet(updates);
    await Promise.all([stripeService.refresh(), paypalService.refresh()]);
    const config = await systemConfig.getAll();
    res.json({
      success: true,
      message: 'System settings updated successfully',
      data: systemConfig.maskAdminConfig(config),
    });
  } catch (err) {
    logger.error(`settings/system PUT failed: ${err.message}`);
    res.status(500).json({ success: false, error: 'Unable to save system settings' });
  }
});

/**
 * POST /api/settings/setup — public (single-use onboarding wizard)
 * Creates the master Super-Admin account (only when no admin exists yet) and
 * persists the buyer's initial business details in one atomic step.
 */
router.post('/setup', async (req, res) => {
  try {
    const { business, currency, admin } = req.body || {};
    if (!admin || typeof admin !== 'object') return invalid(res, 'Super-Admin details are required');

    const name = pickString(admin, 'name', 80);
    const email = pickString(admin, 'email', 120);
    const password = typeof admin.password === 'string' ? admin.password : '';

    if (!name) return invalid(res, 'Admin name is required');
    if (!email || !EMAIL_REGEX.test(email)) return invalid(res, 'Valid admin email is required', 'INVALID_EMAIL');
    if (password.length < 8) return invalid(res, 'Password must be at least 8 characters', 'WEAK_PASSWORD');

    let adminUser = null;
    try {
      adminUser = await User.findOne({ where: { role: 'admin' } });
    } catch (e) {
      logger.warn(`setup: admin lookup failed (${e.message}) — assuming DB unavailable`);
    }

    if (adminUser) {
      return res.status(409).json({
        success: false,
        error: 'Setup already completed. Log in with the existing admin account.',
        code: 'SETUP_COMPLETED',
      });
    }

    const businessName = pickString(business, 'name', 80);
    if (!businessName) return invalid(res, 'Business name is required');

    const currencyCode = pickString(currency, 'code', 3).toUpperCase() || 'USD';
    if (!CURRENCY_LIST[currencyCode]) return invalid(res, `Unsupported currency: ${currencyCode}`, 'INVALID_CURRENCY');

    // Create super-admin
    const hashed = await bcrypt.hash(password, 12);
    const newUser = await User.create({
      name,
      email,
      password: hashed,
      role: 'admin',
      isVerified: true,
      isActive: true,
      betaStatus: 'active',
    });

    // Persist business + currency config and mark setup complete
    await systemConfig.bulkSet({
      business: {
        name: businessName,
        tagline: pickString(business, 'tagline', 140),
        logoUrl: pickString(business, 'logoUrl', 500),
        supportEmail: pickString(business, 'supportEmail', 120),
      },
      currency: { code: currencyCode, symbol: CURRENCY_LIST[currencyCode].symbol },
      setup: {
        completed: true,
        completedAt: new Date().toISOString(),
        superAdminEmail: email,
        businessNiche: pickString(business, 'niche', 60) || '',
      },
    });

    res.status(201).json({
      success: true,
      message: 'Setup complete. Welcome aboard.',
      data: {
        token: generateToken(newUser.id),
        user: { id: newUser.id, name, email, role: 'admin' },
      },
    });
  } catch (err) {
    logger.error(`setup failed: ${err.message}`);
    res.status(500).json({ success: false, error: 'Unable to complete setup' });
  }
});

export default router;