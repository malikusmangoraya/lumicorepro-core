/**
 * TOTP (RFC 6238) Authenticator utilities
 * ----------------------------------------
 * Generate & verify time-based one-time passwords compatible with Google
 * Authenticator / Authy. Used for hardware-app 2FA in addition to the
 * email-based OTP flow.
 */
import crypto from 'crypto';

const STEP_SECONDS = 30;
const WINDOW = 1; // allow ±1 step for clock skew

function base32ToBuffer(base32) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bits = [];
  for (const ch of base32.toUpperCase()) {
    const idx = alphabet.indexOf(ch);
    if (idx === -1) continue;
    bits.push(...Array.from({ length: 5 }, (_, b) => (idx >> (4 - b)) & 1));
  }
  const bytes = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    let v = 0;
    for (let b = 0; b < 8; b++) v = (v << 1) | bits[i + b];
    bytes.push(v);
  }
  return Buffer.from(bytes);
}

/** Generate a random base32 secret (32 chars, 160 bits). */
export function generateSecret(length = 32) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bytes = crypto.randomBytes(length);
  let result = '';
  for (const b of bytes) result += alphabet[b & 31];
  return result.slice(0, length);
}

/** Compute the 6-digit TOTP for a secret at an optional counter (default now). */
export function generateTOTP(secret, counter = Math.floor(Date.now() / 1000 / STEP_SECONDS)) {
  const buf = Buffer.alloc(8);
  buf.writeBigUInt64BE(BigInt(counter), 0);
  const key = base32ToBuffer(secret);
  const hmac = crypto.createHmac('sha1', key).update(buf).digest();
  const offset = hmac[hmac.length - 1] & 0x0f;
  const code =
    ((hmac[offset] & 0x7f) << 24) |
    ((hmac[offset + 1] & 0xff) << 16) |
    ((hmac[offset + 2] & 0xff) << 8) |
    (hmac[offset + 3] & 0xff);
  return (code % 1_000_000).toString().padStart(6, '0');
}

/** Verify a submitted code against a secret (with ±1 step tolerance). */
export function verifyTOTP(secret, code) {
  if (!secret || !code) return false;
  const current = Math.floor(Date.now() / 1000 / STEP_SECONDS);
  for (let i = -WINDOW; i <= WINDOW; i++) {
    if (generateTOTP(secret, current + i) === String(code)) return true;
  }
  return false;
}

/** Build an otpauth:// URI for QR-code enrollment in authenticator apps. */
export function buildOTPAuthURI({ secret, accountName, issuer = process.env.APP_BRAND || 'Your App' }) {
  const label = encodeURIComponent(`${issuer}:${accountName}`);
  return `otpauth://totp/${label}?secret=${secret}&issuer=${encodeURIComponent(issuer)}&algorithm=SHA1&digits=6&period=30`;
}

export default { generateSecret, generateTOTP, verifyTOTP, buildOTPAuthURI };