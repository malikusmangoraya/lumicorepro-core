/**
 * Email Service (nodemailer)
 * --------------------------
 * Sends transactional emails (welcome, password reset, order confirmation).
 * Gracefully no-ops in development when SMTP is not configured, and logs the
 * would-be email instead. Never throws for mail failures — callers can assume
 * best-effort delivery.
 */
import nodemailer from 'nodemailer';
import systemConfig from './systemConfig.service.js';

let transporter = null;

/**
 * Load SMTP credentials from the runtime SystemConfig (DB-backed, cached)
 * with process.env as the startup fallback. Called on every send attempt so
 * the admin panel's saved credentials take effect without a restart.
 */
async function getSmtpConfig() {
  const dbCfg = await systemConfig.get('smtp', null);
  if (dbCfg && dbCfg.enabled && dbCfg.host && dbCfg.user && dbCfg.pass && !dbCfg.host.includes('your_')) {
    return {
      host: dbCfg.host,
      port: dbCfg.port || 587,
      secure: Boolean(dbCfg.secure) || dbCfg.port === 465,
      user: dbCfg.user,
      pass: dbCfg.pass,
      fromName: dbCfg.fromName || '',
      fromEmail: dbCfg.fromEmail || '',
    };
  }
  const configured =
    process.env.SMTP_HOST &&
    process.env.SMTP_USER &&
    process.env.SMTP_PASS &&
    !process.env.SMTP_HOST.includes('your_');
  if (!configured) return null;
  return {
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT) || 587,
    secure: Number(process.env.SMTP_PORT) === 465,
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
    fromName: '',
    fromEmail: '',
  };
}

async function getTransporter() {
  const smtp = await getSmtpConfig();
  if (!smtp) {
    transporter = null;
    return null;
  }

  if (transporter) return transporter;

  transporter = nodemailer.createTransport({
    host: smtp.host,
    port: smtp.port || 587,
    secure: Boolean(smtp.secure),
    auth: { user: smtp.user, pass: smtp.pass },
    pool: true,
    maxConnections: 3,
    rateDelta: 1000,
    rateLimit: 5,
  });

  return transporter;
}

const BRAND = process.env.APP_BRAND || 'Your App';

async function getFromAddress(business = null) {
  const cfg = business || (await systemConfig.get('business', {}));
  const smtp = await systemConfig.get('smtp', {});
  const BizName = cfg.name || BRAND;
  if (smtp.fromEmail) return `"${smtp.fromName || BizName}" <${smtp.fromEmail}>`;
  return `"${BizName}" <${process.env.EMAIL_FROM_ADDRESS || 'no-reply@' + (process.env.APP_DOMAIN || 'yourdomain.com')}>`;
}

/**
 * Send an email. Returns { sent: boolean } — always resolves (never throws).
 */
export async function sendEmail({ to, subject, html, text }) {
  try {
    const tr = await getTransporter();
    if (!tr) {
      // No SMTP configured — log the email content for dev/staging debugging.
      const { logger } = await import('../utils/logger.js');
      logger.info(`[mail:dry-run] to=${to} subject=${subject}`);
      return { sent: false, dryRun: true };
    }

    const from = await getFromAddress();
    await tr.sendMail({ from, to, subject, html: html || text, text });
    return { sent: true };
  } catch (err) {
    const { logger } = await import('../utils/logger.js');
    logger.warn(`Email send failed (${err.message})`);
    return { sent: false, error: err.message };
  }
}

export async function sendWelcomeEmail(to, name) {
  const html = `
    <h2>Welcome, ${name}!</h2>
    <p>Your account has been created successfully.</p>
    <p>Please verify your email to activate your account.</p>
  `;
  return sendEmail({ to, subject: 'Welcome', html });
}

export async function sendPasswordResetEmail(to, token, frontendUrl) {
  const base = frontendUrl || process.env.FRONTEND_URL || 'http://localhost:5173';
  const resetUrl = `${base}/reset-password/${token}`;
  const html = `
    <h2>Password Reset Request</h2>
    <p>You requested to reset your password. Click the link below:</p>
    <p><a href="${resetUrl}">Reset Password</a></p>
    <p>This link expires in 15 minutes.</p>
  `;
  return sendEmail({ to, subject: 'Reset your password', html });
}

export async function sendVerificationEmail(to, name, token, frontendUrl) {
  const base = frontendUrl || process.env.FRONTEND_URL || 'http://localhost:5173';
  const verifyUrl = `${base}/verify-email/${token}`;
  const html = `
    <h2>Verify your email</h2>
    <p>Hi ${name || 'there'}, please confirm your email address to activate your account:</p>
    <p><a href="${verifyUrl}" style="background:#2563eb;color:#fff;padding:12px 20px;border-radius:6px;text-decoration:none;display:inline-block">Verify email</a></p>
    <p>This link expires in 24 hours. If you didn't register on our platform, you can safely ignore this email.</p>
  `;
  return sendEmail({ to, subject: 'Verify your email', html });
}

export async function sendOrderConfirmationEmail(to, { orderNumber, totalPrice, itemsCount }) {
  const html = `
    <h2>Order Confirmed — ${orderNumber}</h2>
    <p>Thank you for your purchase!</p>
    <ul>
      <li>Order: ${orderNumber}</li>
      <li>Items: ${itemsCount}</li>
      <li>Total: $${Number(totalPrice).toFixed(2)}</li>
    </ul>
  `;
  return sendEmail({ to, subject: `Order Confirmed — ${orderNumber}`, html });
}

export async function sendOTPEmail(to, code) {
  const html = `
    <h2>Your Verification Code</h2>
    <p>Use the code below to complete your sign-in (valid for 5 minutes):</p>
    <p style="font-size: 28px; letter-spacing: 4px; font-weight: bold;">${code}</p>
    <p>If you didn't request this, you can safely ignore this email.</p>
  `;
  return sendEmail({ to, subject: 'Your LumicorePro verification code', html });
}

export default { sendEmail, sendWelcomeEmail, sendVerificationEmail, sendPasswordResetEmail, sendOrderConfirmationEmail, sendOTPEmail };