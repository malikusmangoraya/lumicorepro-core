/**
 * Cloudflare Turnstile Captcha Verification (FREE)
 * ------------------------------------------------
 * Server-side verification of Turnstile tokens.
 * Turnstile is free (no billing, unlimited on all plans).
 *
 * Frontend:  import Turnstile from 'react-turnstile'; <Turnstile sitekey="..." />
 * Env vars:
 *   TURNSTILE_SECRET_KEY  — your Turnstile secret key from dash.teams.cloudflare.com
 *   TURNSTILE_ENABLED     — 'true' (default) | 'false' to disable in dev
 */
import logger from '../utils/logger.js';

const TURNSTILE_SECRET = process.env.TURNSTILE_SECRET_KEY || '';
const TURNSTILE_ENABLED = (process.env.TURNSTILE_ENABLED || 'true').toLowerCase() === 'true';

// Cloudflare Turnstile site key for frontend (public, safe to expose)
export const TURNSTILE_SITE_KEY = process.env.TURNSTILE_SITE_KEY || '';

/**
 * Verify a Turnstile token with Cloudflare's siteverify endpoint.
 * Returns { success, error? }
 */
async function verifyTurnstileToken(token, ip) {
  if (!TURNSTILE_SECRET) {
    // No secret configured — skip verification in dev (warn once)
    if (!verifyTurnstileToken._warned) {
      logger.warn('TURNSTILE_SECRET_KEY not set — captcha verification skipped (dev mode)');
      verifyTurnstileToken._warned = true;
    }
    return { success: true };
  }

  try {
    const formData = new URLSearchParams();
    formData.append('secret', TURNSTILE_SECRET);
    formData.append('response', token);
    if (ip) formData.append('remoteip', ip);

    const result = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      body: formData,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const data = await result.json();

    if (!data.success) {
      logger.warn(`Turnstile verification failed: ${JSON.stringify(data['error-codes'] || [])}`);
      return { success: false, error: data['error-codes']?.[0] || 'verification_failed' };
    }

    return { success: true };
  } catch (err) {
    logger.error(`Turnstile verify error: ${err.message}`);
    // Fail open only in dev; in production, fail closed
    if (process.env.NODE_ENV === 'production') {
      return { success: false, error: 'turnstile_unreachable' };
    }
    return { success: true };
  }
}

/**
 * Express middleware: verify Turnstile captcha token from request body.
 * Skipped when TURNSTILE_ENABLED=false or no secret configured (dev mode).
 */
export function requireCaptcha(req, res, next) {
  if (!TURNSTILE_ENABLED || !TURNSTILE_SECRET) {
    return next();
  }

  const token = req.body?.captchaToken || req.body?.cf_turnstile_response || req.headers['x-captcha-token'];

  if (!token || typeof token !== 'string' || token.trim().length < 10) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'CAPTCHA_REQUIRED',
        message: 'Captcha verification required. Please complete the captcha.',
      },
    });
  }

  const ip = req.ip || req.connection?.remoteAddress;
  verifyTurnstileToken(token, ip)
    .then((result) => {
      if (!result.success) {
        return res.status(403).json({
          success: false,
          error: {
            code: 'CAPTCHA_FAILED',
            message: 'Captcha verification failed. Please try again.',
          },
        });
      }
      next();
    })
    .catch((err) => {
      logger.error(`Captcha middleware error: ${err.message}`);
      next(); // fail open in unexpected errors
    });
}

/**
 * Optional captcha — sets req.captchaVerified=true if token present & valid.
 * Does NOT block if token is missing (use for optional protection).
 */
export function optionalCaptcha(req, res, next) {
  if (!TURNSTILE_ENABLED || !TURNSTILE_SECRET) {
    req.captchaVerified = true;
    return next();
  }

  const token = req.body?.captchaToken || req.headers['x-captcha-token'];
  if (!token) {
    req.captchaVerified = false;
    return next();
  }

  const ip = req.ip || req.connection?.remoteAddress;
  verifyTurnstileToken(token, ip)
    .then((result) => {
      req.captchaVerified = result.success;
      next();
    })
    .catch(() => {
      req.captchaVerified = false;
      next();
    });
}

export default { requireCaptcha, optionalCaptcha, TURNSTILE_SITE_KEY };
