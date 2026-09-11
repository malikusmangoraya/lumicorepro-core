import { describe, it, expect } from '@jest/globals';
import refreshService from '../../services/refreshToken.service.js';
import jwt from 'jsonwebtoken';

describe('Refresh token rotation & revocation', () => {
  process.env.JWT_SECRET = 'access_secret_test_12345';
  process.env.JWT_REFRESH_SECRET = 'refresh_secret_test_12345';

  it('generates a signed refresh token carrying jti', () => {
    const { refreshToken, jti, userId } = refreshService.generateRefreshToken(7);
    expect(userId).toBe(7);
    expect(jti).toBeTruthy();
    const decoded = refreshService.verifyRefreshToken(refreshToken);
    expect(decoded.type).toBe('refresh');
    expect(decoded.jti).toBe(jti);
  });

  it('generates a short-lived access token with default expiry', () => {
    const token = refreshService.generateAccessToken(7);
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    expect(decoded.id).toBe(7);
  });

  it('revokes and detects a used token', async () => {
    const { jti, userId } = refreshService.generateRefreshToken(7);
    expect(await refreshService.isRefreshTokenRevoked(jti)).toBe(false);
    await refreshService.revokeRefreshToken(jti, userId);
    expect(await refreshService.isRefreshTokenRevoked(jti)).toBe(true);
  });

  it('revokes an entire family on reuse', async () => {
    const a = refreshService.generateRefreshToken(1);
    const b = refreshService.generateRefreshToken(1);
    const familyId = a.jti; // reuse a's family
    await refreshService.revokeRefreshToken(a.jti, 1, familyId);
    await refreshService.revokeRefreshToken(b.jti, 1, familyId);
    const revokedCount = await refreshService.revokeFamily(familyId);
    expect(revokedCount).toBeGreaterThanOrEqual(1);
  });

  it('rejects a wrong-secret token as invalid', () => {
    const { refreshToken } = refreshService.generateRefreshToken(3);
    process.env.JWT_REFRESH_SECRET = 'changed_secret_123456';
    expect(() => refreshService.verifyRefreshToken(refreshToken)).toThrow();
  });
});