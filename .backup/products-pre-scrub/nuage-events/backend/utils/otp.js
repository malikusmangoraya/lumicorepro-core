import crypto from 'crypto';

/**
 * In-memory / temporary OTP store (Can be backed by Redis in cluster)
 */
const otpStore = new Map();

/**
 * Generate a 6-digit OTP code
 * @param {string} identifier - User email or phone
 * @param {number} ttlMinutes - Expiration in minutes (default: 10)
 * @returns {string} 6-digit OTP code
 */
export const generateOTP = (identifier, ttlMinutes = 10) => {
  const code = Math.floor(100000 + Math.random() * 900000).toString();
  const expiresAt = Date.now() + ttlMinutes * 60 * 1000;

  // Hash code for secure storage
  const hash = crypto.createHash('sha256').update(code).digest('hex');

  otpStore.set(identifier, {
    hash,
    expiresAt,
    attempts: 0,
  });

  return code;
};

/**
 * Verify OTP code
 * @param {string} identifier - User email or phone
 * @param {string} code - Submitted OTP code
 * @returns {boolean} Whether the code is valid
 */
export const verifyOTP = (identifier, code) => {
  const record = otpStore.get(identifier);
  if (!record) return false;

  if (Date.now() > record.expiresAt) {
    otpStore.delete(identifier);
    return false;
  }

  if (record.attempts >= 5) {
    otpStore.delete(identifier);
    return false;
  }

  record.attempts += 1;
  const hash = crypto.createHash('sha256').update(code).digest('hex');

  if (record.hash === hash) {
    otpStore.delete(identifier);
    return true;
  }

  return false;
};
