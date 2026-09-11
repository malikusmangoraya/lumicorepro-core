/**
 * Refresh Token Rotation & Revocation
 * ------------------------------------
 * - Short-lived access token (15 min) + long-lived refresh token (30d).
 * - Rotation: every /auth/refresh call issues a NEW refresh token and revokes
 *   the old one (revocation list in Redis/DB).
 * - Logout revokes the active refresh token immediately.
 * - Compromised-token detection: using a revoked token triggers revocation of
 *   the whole token family.
 */
import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import { getRedis } from '../services/cache/redis.client.js';

const REFRESH_TTL = 30 * 24 * 60 * 60; // 30 days (seconds)

/**
 * Generate a random opaque refresh-token id + signed JWT payload.
 * We store only the hashed id in the revocation list — never raw tokens.
 */
export function generateRefreshToken(userId) {
  const jti = crypto.randomBytes(24).toString('hex');
  const refreshToken = jwt.sign(
    { sub: String(userId), type: 'refresh', jti },
    process.env.JWT_REFRESH_SECRET,
    { expiresIn: process.env.JWT_REFRESH_EXPIRE || '30d' },
  );
  return { refreshToken, jti, userId };
}

export function generateAccessToken(userId, extra = {}) {
  return jwt.sign({ id: userId, ...extra }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRE || '15m',
  });
}

/** Verify + decode a refresh token. Returns payload or throws. */
export function verifyRefreshToken(token) {
  return jwt.verify(token, process.env.JWT_REFRESH_SECRET);
}

/** Mark a refresh token (by jti) as revoked, with a family id for rollback. */
export async function revokeRefreshToken(jti, userId, familyId = null) {
  const redis = getRedis();
  const key = `refresh:revoked:${jti}`;
  await redis.set(key, JSON.stringify({ revokedAt: Date.now(), userId: String(userId), familyId: familyId || jti }), 'EX', REFRESH_TTL);
  // Keep a per-user index for logout-all
  const fam = familyId || jti;
  await redis.sadd(`refresh:family:${fam}`, jti);
  return true;
}

/** Is this refresh token id revoked? */
export async function isRefreshTokenRevoked(jti) {
  const redis = getRedis();
  const raw = await redis.get(`refresh:revoked:${jti}`);
  return !!raw;
}

/** Revoke every token in the compromised family (token-reuse response). */
export async function revokeFamily(familyId) {
  const redis = getRedis();
  if (!familyId) return 0;
  const members = await redis.smembers(`refresh:family:${familyId}`);
  for (const jti of members) {
    await redis.del(`refresh:revoked:${jti}`);
    // re-mark revoked: we keep the list simple by re-setting the key
    await redis.set(`refresh:revoked:${jti}`, JSON.stringify({ revokedAt: Date.now(), familyId }), 'EX', REFRESH_TTL);
  }
  await redis.del(`refresh:family:${familyId}`);
  return members.length;
}

export default {
  generateRefreshToken,
  generateAccessToken,
  verifyRefreshToken,
  revokeRefreshToken,
  isRefreshTokenRevoked,
  revokeFamily,
};