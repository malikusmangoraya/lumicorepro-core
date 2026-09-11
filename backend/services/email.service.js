/**
 * Email Service (nodemailer)
 * --------------------------
 * Sends transactional emails (welcome, password reset, order confirmation).
 * Gracefully no-ops in development when SMTP is not configured, and logs the
 * would-be email instead. Never throws for mail failures — callers can assume
 * best-effort delivery.
 */
import nodemailer from 'nodemailer';

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;

  const configured = process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS;
  if (!configured) {
    transporter = null;
    return null;
  }

  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT) || 587,
    secure: Number(process.env.SMTP_PORT) === 465,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
    pool: true,
    maxConnections: 3,
    rateDelta: 1000,
    rateLimit: 5,
  });

  return transporter;
}

const BRAND = process.env.APP_BRAND || 'Your App';
const FROM = process.env.EMAIL_FROM || `"${BRAND}" <no-reply@${process.env.APP_DOMAIN || 'yourdomain.com'}>`;

/**
 * Send an email. Returns { sent: boolean } — always resolves (never throws).
 */
export async function sendEmail({ to, subject, html, text }) {
  try {
    const tr = getTransporter();
    if (!tr) {
      // No SMTP configured — log the email content for dev/staging debugging.
      const { logger } = await import('../utils/logger.js');
      logger.info(`[mail:dry-run] to=${to} subject=${subject}`);
      return { sent: false, dryRun: true };
    }

    await tr.sendMail({ from: FROM, to, subject, html: html || text, text });
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