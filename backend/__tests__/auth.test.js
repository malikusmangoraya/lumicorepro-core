import { describe, it, expect } from '@jest/globals';
import { generateOTP, verifyOTP } from '../utils/otp.js';

describe('Auth & 2FA OTP Utilities', () => {
  describe('2FA OTP Generation & Verification', () => {
    it('should generate a 6-digit OTP code', () => {
      const email = 'alex@example.com';
      const otp = generateOTP(email, 10);
      expect(otp).toHaveLength(6);
      expect(/^\d{6}$/.test(otp)).toBe(true);
    });

    it('should verify valid OTP code correctly', () => {
      const email = 'alex_verify@example.com';
      const otp = generateOTP(email, 10);
      const isValid = verifyOTP(email, otp);
      expect(isValid).toBe(true);
    });

    it('should reject incorrect OTP code', () => {
      const email = 'alex_fail@example.com';
      generateOTP(email, 10);
      const isValid = verifyOTP(email, '000000');
      expect(isValid).toBe(false);
    });
  });
});
