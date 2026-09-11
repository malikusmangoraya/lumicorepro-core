import express from 'express';
import { Op } from 'sequelize';
import { body, validationResult } from 'express-validator';
import crypto from 'crypto';
import bcrypt from 'bcryptjs';
import User from '../models/User.js';
import { protect, generateToken, registerInMemoryStore } from '../middleware/auth.js';
import { authLimiter } from '../middleware/rateLimit.js';
import { requireCaptcha, optionalCaptcha } from '../middleware/captchaVerify.js';
import refreshService from '../services/refreshToken.service.js';
import logger from '../utils/logger.js';
import { generateOTP, verifyOTP } from '../utils/otp.js';
import { generateSecret, verifyTOTP, buildOTPAuthURI } from '../utils/totp.js';
import { sendPasswordResetEmail, sendVerificationEmail, sendOTPEmail } from '../services/email.service.js';
import { enqueue, QUEUES } from '../services/queue/queue.service.js';
import passport from 'passport';
import { recordAudit } from '../middleware/audit.js';
import { validateRequest } from '../middleware/validateRequest.js';
import { registerSchema, loginSchema, changePasswordSchema, forgotPasswordSchema } from '../middleware/validations/index.js';

const router = express.Router();

// ── In-Memory Development / Offline Fallback Store ──────────────────────────
const inMemoryUsers = new Map();

// Register the store with auth middleware so protect() can use it as fallback
registerInMemoryStore(inMemoryUsers);

// Seed default users for immediate out-of-the-box local testing
(async () => {
  const hash = await bcrypt.hash('Password123!', 10);
  const demoUsers = [
    {
      id: 1,
      name: 'Demo User',
      email: 'demo@lumicorepro.com',
      password: hash,
      role: 'user',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
      isActive: true,
      twoFactorEnabled: false,
      preferences: { theme: 'dark', language: 'en' },
    },
    {
      id: 2,
      name: 'Admin User',
      email: 'admin@lumicorepro.com',
      password: hash,
      role: 'admin',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
      isActive: true,
      twoFactorEnabled: false,
      preferences: { theme: 'dark', language: 'en' },
    },
  ];
  for (const u of demoUsers) {
    inMemoryUsers.set(u.email.toLowerCase(), {
      ...u,
      comparePassword: async function (cand) { return bcrypt.compare(cand, this.password); },
      save: async function () { return this; },
    });
  }
})();

async function findUserByEmail(email) {
  const normEmail = email.toLowerCase().trim();
  try {
    const user = await User.scope('withPassword').findOne({ where: { email: normEmail } });
    if (user) return user;
  } catch (err) {
    logger.warn(`Postgres query failed, falling back to memory store: ${err.message}`);
  }
  return inMemoryUsers.get(normEmail) || null;
}

async function findUserById(id) {
  try {
    const user = await User.findByPk(id);
    if (user) return user;
  } catch (err) {
    logger.warn(`Postgres query failed, falling back to memory store: ${err.message}`);
  }
  for (const u of inMemoryUsers.values()) {
    if (String(u.id) === String(id)) return u;
  }
  return null;
}

/* ══════════════════════════════════════════════════════════════════
 * REGISTER
 * ══════════════════════════════════════════════════════════════════ */
router.post(
  '/register',
  authLimiter,
  requireCaptcha,
  validateRequest(registerSchema),
  async (req, res, next) => {
    try {
      const { name, email, password, role } = req.body;
      const normEmail = email.toLowerCase().trim();

      const existingUser = await findUserByEmail(normEmail);
      if (existingUser) {
        return res.status(400).json({
          success: false,
          error: 'User already exists with this email',
        });
      }

      let user;
      // Waitlist/Beta gate: when WAITLIST_MODE=true, new signups enter the
      // waitlist unless the daily auto-approve cap is still available.
      const waitlistEnabled = process.env.WAITLIST_MODE === 'true';
      let betaStatus = 'active';
      if (waitlistEnabled) {
        const autoApproveCap = parseInt(process.env.WAITLIST_AUTO_APPROVE_DAILY, 10) || 0;
        const approvedToday = await User.count({
          where: {
            betaStatus: 'active',
            createdAt: { [Op.gte]: new Date(new Date().setUTCHours(0, 0, 0, 0)) },
          },
        });
        betaStatus = approvedToday < autoApproveCap ? 'active' : 'waitlist';
      }
      try {
        user = await User.create({
          name,
          email: normEmail,
          password,
          role: role === 'vendor' ? 'vendor' : 'user',
          betaStatus,
        });
      } catch (err) {
        logger.warn(`Postgres insert failed, storing user in memory: ${err.message}`);
        const hashedPassword = await bcrypt.hash(password, 12);
        user = {
          id: Date.now(),
          name,
          email: normEmail,
          password: hashedPassword,
          role: role === 'vendor' ? 'vendor' : 'user',
          avatar: '',
          isActive: true,
          betaStatus,
          twoFactorEnabled: false,
          preferences: { theme: 'dark', language: 'en' },
          comparePassword: async function (cand) { return bcrypt.compare(cand, this.password); },
          save: async function () { return this; },
        };
        inMemoryUsers.set(normEmail, user);
      }

      const token = generateToken(user.id);
      const rotated = refreshService.generateRefreshToken(user.id);
      res.cookie('refresh_token', rotated.refreshToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 30 * 24 * 60 * 60 * 1000,
        path: '/api/auth',
      });
      logger.info(`New user registered: ${user.email} (${user.id})`);
      recordAudit(req, { action: 'auth.register', userId: user.id, email: user.email });

      // One-time email verification token (DB users only; demo/memory users skip).
      if (typeof user.update === 'function') {
        const verificationToken = crypto.randomBytes(32).toString('hex');
        await user.update({
          verificationToken,
          verificationExpires: new Date(Date.now() + 24 * 60 * 60 * 1000),
        });
        sendVerificationEmail(user.email, user.name, verificationToken);
      }
      enqueue(QUEUES.EMAIL, {
        to: user.email,
        subject: 'Welcome',
        html: `<h2>Welcome, ${user.name}!</h2><p>Your account has been created successfully.</p>`,
      });

      res.status(201).json({
        success: true,
        token,
        refreshToken: rotated.refreshToken,
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role,
          avatar: user.avatar || '',
          preferences: user.preferences || {},
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * LOGIN
 * ══════════════════════════════════════════════════════════════════ */
router.post(
  '/login',
  authLimiter,
  optionalCaptcha,
  validateRequest(loginSchema),
  async (req, res, next) => {
    try {
      const { email, password } = req.body;
      const user = await findUserByEmail(email);

      if (!user) {
        return res.status(401).json({ success: false, error: 'Invalid credentials' });
      }

      if (user.isActive === false) {
        return res.status(401).json({
          success: false,
          error: 'Account has been deactivated. Please contact support.',
        });
      }

      const isMatch = await user.comparePassword(password);
      if (!isMatch) {
        recordAudit(req, { action: 'auth.login.failure', email: req.body?.email });
        return res.status(401).json({ success: false, error: 'Invalid credentials' });
      }

      user.lastLogin = new Date();
      if (typeof user.save === 'function') {
        try {
          await user.save({ validateBeforeSave: false });
        } catch {
          /* ignore */
        }
      }

      if (user.twoFactorEnabled) {
        const { code } = generateOTP(user.email);
        logger.info(`2FA OTP sent to ${user.email} during login`);
        sendOTPEmail(user.email, code);

        return res.json({
          success: true,
          requires2FA: true,
          message: 'Two-factor authentication required. OTP sent to your email.',
          user: { id: user.id, name: user.name, email: user.email },
        });
      }

      const token = generateToken(user.id);
      const rotated = refreshService.generateRefreshToken(user.id);
      res.cookie('refresh_token', rotated.refreshToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 30 * 24 * 60 * 60 * 1000,
        path: '/api/auth',
      });
      logger.info(`User logged in: ${user.email}`);
      recordAudit(req, { action: 'auth.login.success', userId: user.id, email: user.email });

      res.json({
        success: true,
        token,
        refreshToken: rotated.refreshToken,
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role,
          avatar: user.avatar || '',
          preferences: user.preferences || {},
          twoFactorEnabled: !!user.twoFactorEnabled,
          betaStatus: user.betaStatus || 'active',
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * LOGOUT (revokes the active refresh token)
 * ══════════════════════════════════════════════════════════════════ */
router.post('/logout', async (req, res, next) => {
  try {
    const refreshToken = req.cookies?.refresh_token || req.body?.refreshToken;
    if (refreshToken) {
      try {
        const payload = refreshService.verifyRefreshToken(refreshToken);
        if (payload?.jti) {
          const family = payload.familyId || payload.jti;
          await refreshService.revokeRefreshToken(payload.jti, payload.sub, family);
        }
      } catch {
        /* token already expired/revoked — nothing to revoke */
      }
    }
    res.clearCookie('refresh_token', { path: '/api/auth' });
    recordAudit(req, { action: 'auth.logout', userId: req.user?.id, email: req.user?.email });
    return res.json({ success: true, message: 'Logged out successfully' });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * PROFILE  GET / PUT
 * ══════════════════════════════════════════════════════════════════ */
router.get('/profile', protect, async (req, res, next) => {
  try {
    const user = await findUserById(req.user.id);
    if (!user) return res.status(404).json({ success: false, error: 'User not found' });
    const userObj = typeof user.toJSON === 'function' ? user.toJSON() : { ...user };
    delete userObj.password;
    res.json({ success: true, user: userObj });
  } catch (error) {
    next(error);
  }
});

router.put(
  '/profile',
  protect,
  [
    body('name').optional().trim().notEmpty().withMessage('Name cannot be empty'),
    body('phone').optional().trim(),
  ],
  async (req, res, next) => {
    try {
      const updates = {};
      const allowedFields = ['name', 'phone', 'avatar', 'address', 'preferences'];
      allowedFields.forEach((field) => {
        if (req.body[field] !== undefined) updates[field] = req.body[field];
      });

      const user = await findUserById(req.user.id);
      if (!user) return res.status(404).json({ success: false, error: 'User not found' });

      if (typeof user.update === 'function') {
        await user.update(updates);
      } else {
        Object.assign(user, updates);
      }

      const userObj = typeof user.toJSON === 'function' ? user.toJSON() : { ...user };
      delete userObj.password;
      res.json({ success: true, user: userObj });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * REFRESH TOKEN (rotation + revocation)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * Issue a fresh access token + a NEW rotating refresh token (httpOnly cookie).
 * The previous refresh token is revoked on every rotation.
 */
router.post('/refresh', authLimiter, async (req, res, next) => {
  try {
    const oldRefresh = req.cookies?.refresh_token || req.body?.refreshToken;
    if (!oldRefresh) {
      return res.status(401).json({ success: false, error: 'No refresh token provided' });
    }

    // 1. Verify the incoming refresh token
    let payload;
    try {
      payload = refreshService.verifyRefreshToken(oldRefresh);
    } catch {
      return res.status(401).json({ success: false, error: 'Invalid or expired refresh token' });
    }
    if (payload.type !== 'refresh') {
      return res.status(401).json({ success: false, error: 'Invalid token type' });
    }

    // 2. Reuse detection: if it's already revoked, the whole family is compromised
    const alreadyRevoked = await refreshService.isRefreshTokenRevoked(payload.jti);
    if (alreadyRevoked) {
      logger.warn(`Refresh token reuse detected for user ${payload.sub}, revoking family`);
      await refreshService.revokeFamily(payload.familyId || payload.jti);
      return res.status(401).json({ success: false, error: 'Refresh token has been revoked. Please log in again.' });
    }

    // 3. Verify the user still exists + active
    const user = await findUserById(payload.sub);
    if (!user || user.isActive === false) {
      return res.status(401).json({ success: false, error: 'Account is not active' });
    }

    // 4. Rotation: revoke the old, issue a new refresh token (same family)
    const familyId = payload.familyId || payload.jti;
    await refreshService.revokeRefreshToken(payload.jti, payload.sub, familyId);
    const rotated = refreshService.generateRefreshToken(user.id);

    const accessToken = refreshService.generateAccessToken(user.id);

    // httpOnly refresh cookie for browsers
    res.cookie('refresh_token', rotated.refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 30 * 24 * 60 * 60 * 1000,
      path: '/api/auth',
    });

    return res.json({
      success: true,
      token: accessToken,
      refreshToken: rotated.refreshToken, // for clients that store it themselves
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
        avatar: user.avatar || '',
      },
    });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * 2FA — SETUP & VERIFY
 * ══════════════════════════════════════════════════════════════════ */
router.post('/2fa/setup', protect, async (req, res, next) => {
  try {
    const user = await findUserById(req.user.id);
    if (!user) return res.status(404).json({ success: false, error: 'User not found' });

    if (user.twoFactorEnabled) {
      return res.status(400).json({ success: false, error: '2FA is already enabled' });
    }

    const secret = crypto.randomBytes(10).toString('base32').slice(0, 16).toUpperCase();
    user.twoFactorEnabled = true;
    user.twoFactorSecret = secret;
    user.twoFactorMethod = req.body.method || 'email';
    if (req.body.phone) user.twoFactorPhone = req.body.phone;
    user.twoFactorActivatedAt = null;
    if (typeof user.save === 'function') await user.save();

    const otp = generateOTP(user.email);
    logger.info(`2FA setup initiated for ${user.email}`);
    recordAudit(req, { action: 'auth.2fa.setup', userId: user.id, email: user.email });

    res.json({
      success: true,
      message: '2FA setup initiated. Verify with the OTP sent to your email via /2fa/confirm.',
      twoFactorSecret: secret,
      twoFactorMethod: user.twoFactorMethod,
      ...(process.env.NODE_ENV !== 'production' && { debugOtp: otp }),
    });
  } catch (error) {
    next(error);
  }
});

router.post(
  '/2fa/confirm',
  protect,
  [body('otp').isLength({ min: 6, max: 6 }).withMessage('6-digit OTP is required')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const isValid = verifyOTP(req.user.email, req.body.otp);
      if (!isValid) {
        return res.status(400).json({ success: false, error: 'Invalid or expired OTP' });
      }

      const user = await findUserById(req.user.id);
      if (!user) return res.status(404).json({ success: false, error: 'User not found' });

      user.twoFactorActivatedAt = new Date();
      if (typeof user.save === 'function') await user.save();

      logger.info(`2FA confirmed and activated for ${user.email}`);
      recordAudit(req, { action: 'auth.2fa.enable', userId: user.id, email: user.email });
      res.json({ success: true, message: 'Two-factor authentication is now active' });
    } catch (error) {
      next(error);
    }
  }
);

router.post('/2fa/send-otp', protect, async (req, res, next) => {
  try {
    const user = await findUserById(req.user.id);
    if (!user) return res.status(404).json({ success: false, error: 'User not found' });

    const otp = generateOTP(user.email);
    logger.info(`2FA OTP resent for ${user.email}`);
    sendOTPEmail(user.email, otp);

    res.json({
      success: true,
      message: `2FA verification code sent to ${user.email}`,
      ...(process.env.NODE_ENV !== 'production' && { debugOtp: otp }),
    });
  } catch (error) {
    next(error);
  }
});

router.post(
  '/2fa/login-verify',
  [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('otp').isLength({ min: 6, max: 6 }).withMessage('6-digit OTP is required'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { email, otp } = req.body;
      const user = await findUserByEmail(email);

      if (!user) {
        return res.status(401).json({ success: false, error: 'Invalid credentials' });
      }

      if (!user.twoFactorEnabled) {
        return res.status(400).json({ success: false, error: '2FA is not enabled for this account' });
      }

      const isValid = verifyOTP(email, otp);
      if (!isValid) {
        return res.status(401).json({ success: false, error: 'Invalid or expired 2FA code' });
      }

      user.lastLogin = new Date();
      if (typeof user.save === 'function') await user.save({ validateBeforeSave: false });

      const token = generateToken(user.id);
      logger.info(`2FA login verified for ${user.email}`);
      recordAudit(req, { action: 'auth.2fa.login_verify', userId: user.id, email: user.email });

      res.json({
        success: true,
        message: '2FA verification successful',
        token,
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role,
          avatar: user.avatar || '',
          preferences: user.preferences || {},
          twoFactorEnabled: user.twoFactorEnabled,
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * 2FA — AUTHENTICATOR APP (TOTP)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /api/auth/2fa/authenticator/setup
 * Generate a TOTP secret + otpauth URI for scanning with an authenticator app.
 * Returns 2FA only (not enabled yet) until confirmed via /2fa/authenticator/confirm.
 */
router.post('/2fa/authenticator/setup', protect, async (req, res, next) => {
  try {
    const user = await findUserById(req.user.id);
    if (!user) return res.status(404).json({ success: false, error: 'User not found' });

    const secret = generateSecret();
    user.twoFactorSecret = secret;
    user.twoFactorMethod = 'authenticator';
    if (typeof user.save === 'function') await user.save();

    const otpauthUrl = buildOTPAuthURI({
      secret,
      accountName: user.email,
      issuer: process.env.APP_BRAND || 'Your App',
    });

    logger.info(`Authenticator 2FA setup initiated for ${user.email}`);
    res.json({
      success: true,
      message: 'Scan the QR URI with your authenticator app, then confirm the code.',
      secret,
      otpauthUrl,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/auth/2fa/authenticator/confirm
 * Verify a TOTP code from the authenticator app and activate 2FA.
 */
router.post(
  '/2fa/authenticator/confirm',
  protect,
  [body('code').isLength({ min: 6, max: 6 }).withMessage('6-digit code is required')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const user = await findUserById(req.user.id);
      if (!user) return res.status(404).json({ success: false, error: 'User not found' });
      if (!user.twoFactorSecret) {
        return res.status(400).json({ success: false, error: 'No authenticator secret configured. Call setup first.' });
      }

      if (!verifyTOTP(user.twoFactorSecret, req.body.code)) {
        return res.status(400).json({ success: false, error: 'Invalid authenticator code' });
      }

      user.twoFactorEnabled = true;
      user.twoFactorMethod = 'authenticator';
      user.twoFactorActivatedAt = new Date();
      if (typeof user.save === 'function') await user.save();

      logger.info(`Authenticator 2FA activated for ${user.email}`);
      recordAudit(req, { action: 'auth.2fa.enable', userId: user.id, email: user.email });
      res.json({ success: true, message: 'Two-factor authentication is now active' });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * POST /api/auth/2fa/authenticator/verify
 * Verify a TOTP code during login (used when method === 'authenticator').
 * Returns a JWT on success.
 */
router.post(
  '/2fa/authenticator/verify',
  [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('code').isLength({ min: 6, max: 6 }).withMessage('6-digit code is required'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { email, code } = req.body;
      const user = await findUserByEmail(email);
      if (!user) return res.status(401).json({ success: false, error: 'Invalid credentials' });
      if (!user.twoFactorEnabled || user.twoFactorMethod !== 'authenticator') {
        return res.status(400).json({ success: false, error: 'Authenticator 2FA is not enabled for this account' });
      }

      if (!verifyTOTP(user.twoFactorSecret, code)) {
        return res.status(401).json({ success: false, error: 'Invalid or expired authenticator code' });
      }

      const token = generateToken(user.id);
      logger.info(`Authenticator 2FA verified for ${user.email}`);
      recordAudit(req, { action: 'auth.2fa.login_verify', userId: user.id, email: user.email });

      res.json({
        success: true,
        message: '2FA verification successful',
        token,
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role,
          avatar: user.avatar || '',
          preferences: user.preferences || {},
          twoFactorEnabled: user.twoFactorEnabled,
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * CHANGE PASSWORD (authenticated)
 * ══════════════════════════════════════════════════════════════════ */
router.put(
  '/change-password',
  protect,
  [
    body('currentPassword').notEmpty().withMessage('Current password is required'),
    body('newPassword')
      .isLength({ min: 6 })
      .withMessage('New password must be at least 6 characters')
      .custom((val, { req }) => {
        if (val === req.body.currentPassword) {
          throw new Error('New password must differ from current password');
        }
        return true;
      }),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { currentPassword, newPassword } = req.body;

      let user = await findUserById(req.user.id);
      if (!user) return res.status(404).json({ success: false, error: 'User not found' });

      // Verify current password
      const isMatch = typeof user.comparePassword === 'function'
        ? await user.comparePassword(currentPassword)
        : await bcrypt.compare(currentPassword, user.password);

      if (!isMatch) {
        return res.status(400).json({ success: false, error: 'Current password is incorrect' });
      }

      const newHash = await bcrypt.hash(newPassword, 12);

      if (typeof user.update === 'function') {
        await user.update({ password: newHash });
      } else {
        // In-memory fallback
        user.password = newHash;
        if (typeof user.save === 'function') await user.save();
      }

      logger.info(`Password changed for user ${req.user.id}`);
      recordAudit(req, { action: 'auth.password.change', userId: req.user.id, email: req.user?.email });

      res.json({ success: true, message: 'Password changed successfully' });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * EMAIL VERIFICATION
 * ══════════════════════════════════════════════════════════════════ */

/**
 * GET /api/auth/verify-email/:token
 * Verify a user's email address using a token sent by email.
 */
router.get('/verify-email/:token', async (req, res, next) => {
  try {
    const { token } = req.params;

    if (!token || token.length < 16) {
      return res.status(400).json({ success: false, error: 'Invalid verification token' });
    }

    // Look up the unexpired, one-time token persisted on the user row.
    let verified = false;
    try {
      const user = await User.findOne({
        where: {
          verificationToken: token,
          verificationExpires: { [Op.gt]: new Date() },
        },
      });
      if (user) {
        await user.update({ isVerified: true, verificationToken: null, verificationExpires: null });
        verified = true;
        logger.info(`Email verified for user ${user.email}`);
        recordAudit(req, { action: 'auth.email.verified', userId: user.id, email: user.email });
      }
    } catch (dbErr) {
      logger.warn(`DB verify-email error: ${dbErr.message}`);
    }

    // Friendly redirect or JSON response
    if (req.headers.accept?.includes('text/html')) {
      return res.redirect(`${process.env.FRONTEND_URL || 'http://localhost:5173'}/login?verified=true`);
    }

    res.status(verified ? 200 : 400).json({
      success: verified,
      message: verified
        ? 'Email verified successfully. You can now log in.'
        : 'Verification token is invalid or has expired.',
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/auth/resend-verification
 * Re-send the verification email.
 */
router.post(
  '/resend-verification',
  [body('email').isEmail().normalizeEmail().withMessage('Valid email is required')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const user = await findUserByEmail(req.body.email);
      if (user && !user.isVerified && typeof user.update === 'function') {
        const token = crypto.randomBytes(32).toString('hex');
        await user.update({
          verificationToken: token,
          verificationExpires: new Date(Date.now() + 24 * 60 * 60 * 1000),
        });
        sendVerificationEmail(user.email, user.name, token);
        logger.info(`Verification email resent to ${req.body.email}`);
        recordAudit(req, { action: 'auth.verification.resent', email: req.body.email });
        return res.json({ success: true, message: 'Verification email sent.' });
      }

      res.json({
        success: true,
        message: 'If an unverified account exists, a new verification email has been sent.',
      });
    } catch (error) {
      next(error);
    }
  }
);

/* ══════════════════════════════════════════════════════════════════
 * FORGOT / RESET PASSWORD
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /api/auth/forgot-password
 * Send a password-reset email with a one-time, expiring token persisted on the
 * user row (so the flow survives restarts and multiple instances).
 */
router.post(
  '/forgot-password',
  authLimiter,
  [body('email').isEmail().normalizeEmail().withMessage('Valid email is required')],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const user = await findUserByEmail(req.body.email);
      if (user && user.email && typeof user.update === 'function') {
        const token = crypto.randomBytes(32).toString('hex');
        await user.update({
          resetPasswordToken: token,
          resetPasswordExpires: new Date(Date.now() + 15 * 60 * 1000),
        });
        sendPasswordResetEmail(user.email, token);
        logger.info(`Password reset email sent to ${user.email}`);
        recordAudit(req, { action: 'auth.password.forgot', email: user.email });
      }

      // Always return 200 to avoid user enumeration
      res.json({
        success: true,
        message: 'If an account exists for this email, a password reset link has been sent.',
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * Apply a reset token. Shared by the path-token route (email link) and the
 * body-token route (API clients). Returns the updated user or null.
 */
async function applyPasswordReset(token, password) {
  const user = await User.findOne({
    where: {
      resetPasswordToken: token,
      resetPasswordExpires: { [Op.gt]: new Date() },
    },
  });
  if (!user) return null;
  await user.update({
    password,
    resetPasswordToken: null,
    resetPasswordExpires: null,
  });
  return user;
}

const resetPasswordValidation = [body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters')];

/**
 * POST /api/auth/reset-password/:token
 * Token comes from the emailed reset link path.
 */
router.post('/reset-password/:token', authLimiter, resetPasswordValidation, async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ success: false, errors: errors.array() });
    }

    const user = await applyPasswordReset(req.params.token, req.body.password);
    if (!user) {
      return res.status(400).json({ success: false, error: 'Reset link is invalid or has expired' });
    }

    logger.info(`Password reset for user ${user.email}`);
    recordAudit(req, { action: 'auth.password.reset', userId: user.id, email: user.email });
    res.json({ success: true, message: 'Password reset successfully. You can now log in.' });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/auth/reset-password
 * Token supplied in the body (programmatic clients).
 */
router.post('/reset-password', authLimiter, [
  body('token').notEmpty().withMessage('Reset token is required'),
  ...resetPasswordValidation,
], async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ success: false, errors: errors.array() });
    }

    const user = await applyPasswordReset(req.body.token, req.body.password);
    if (!user) {
      return res.status(400).json({ success: false, error: 'Reset link is invalid or has expired' });
    }

    logger.info(`Password reset for user ${user.email}`);
    recordAudit(req, { action: 'auth.password.reset', userId: user.id, email: user.email });
    res.json({ success: true, message: 'Password reset successfully. You can now log in.' });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * OAUTH (Google / GitHub via Passport)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * GET /api/auth/oauth/google
 * Kick off Google OAuth flow.
 */
router.get('/oauth/google', (req, res, next) => {
  passport.authenticate('google', { scope: ['profile', 'email'] })(req, res, next);
});

/**
 * GET /api/auth/oauth/google/callback
 * Google OAuth callback → issues our JWT via redirect to frontend.
 */
router.get(
  '/oauth/google/callback',
  (req, res, next) => {
    passport.authenticate('google', { session: false }, (err, user) => {
      if (err || !user) {
        return res.redirect(`${process.env.FRONTEND_URL || 'http://localhost:5173'}/login?oauth=error`);
      }
      const token = generateToken(user.id);
      res.redirect(
        `${process.env.FRONTEND_URL || 'http://localhost:5173'}/oauth/callback?token=${token}` +
          `&name=${encodeURIComponent(user.name || '')}&email=${encodeURIComponent(user.email || '')}`
      );
    })(req, res, next);
  }
);

/**
 * GET /api/auth/oauth/github
 * Kick off GitHub OAuth flow.
 */
router.get('/oauth/github', (req, res, next) => {
  passport.authenticate('github', { scope: ['user:email'] })(req, res, next);
});

/**
 * GET /api/auth/oauth/github/callback
 * GitHub OAuth callback → issues our JWT via redirect to frontend.
 */
router.get(
  '/oauth/github/callback',
  (req, res, next) => {
    passport.authenticate('github', { session: false }, (err, user) => {
      if (err || !user) {
        return res.redirect(`${process.env.FRONTEND_URL || 'http://localhost:5173'}/login?oauth=error`);
      }
      const token = generateToken(user.id);
      res.redirect(
        `${process.env.FRONTEND_URL || 'http://localhost:5173'}/oauth/callback?token=${token}` +
          `&name=${encodeURIComponent(user.name || '')}&email=${encodeURIComponent(user.email || '')}`
      );
    })(req, res, next);
  }
);

export default router;
