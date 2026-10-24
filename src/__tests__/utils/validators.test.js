import { describe, it, expect } from 'vitest';
import {
  isEmail,
  isPhone,
  isURL,
  isStrongPassword,
  isAlphanumeric,
  isRequired,
  validateEmail,
  validatePassword,
  validatePhone,
  validateForm,
} from '../../utils/validators';

describe('validators', () => {
  describe('isEmail', () => {
    it('accepts valid addresses', () => {
      expect(isEmail('user@example.com')).toBe(true);
      expect(isEmail('a.b+tag@sub.domain.co')).toBe(true);
    });
    it('rejects malformed addresses', () => {
      expect(isEmail('not-an-email')).toBe(false);
      expect(isEmail('a@b')).toBe(false);
      expect(isEmail('a b@c.com')).toBe(false);
    });
  });

  describe('isPhone', () => {
    it('accepts international formats', () => {
      expect(isPhone('+92 300 1234567')).toBe(true);
      expect(isPhone('(555) 123-4567')).toBe(true);
    });
    it('rejects short or lettered input', () => {
      expect(isPhone('12345')).toBe(false);
      expect(isPhone('call me maybe')).toBe(false);
    });
  });

  describe('isURL', () => {
    it('accepts absolute URLs', () => {
      expect(isURL('https://example.com/path?q=1')).toBe(true);
    });
    it('rejects plain strings', () => {
      expect(isURL('example.com')).toBe(false);
    });
  });

  describe('isStrongPassword', () => {
    it('requires 8+ chars with upper, lower and digit', () => {
      expect(isStrongPassword('Abcdefg1')).toBe(true);
      expect(isStrongPassword('abcdefg1')).toBe(false);
      expect(isStrongPassword('ABCDEFG1')).toBe(false);
      expect(isStrongPassword('Abcdefgh')).toBe(false);
      expect(isStrongPassword('Abc1')).toBe(false);
    });
  });

  describe('isAlphanumeric / isRequired', () => {
    it('isAlphanumeric rejects symbols', () => {
      expect(isAlphanumeric('abc123')).toBe(true);
      expect(isAlphanumeric('abc-123')).toBe(false);
    });
    it('isRequired treats false/0 as present, empty as missing', () => {
      expect(isRequired(false)).toBe(true);
      expect(isRequired(0)).toBe(true);
      expect(isRequired('')).toBe(false);
      expect(isRequired('   ')).toBe(false);
      expect(isRequired(null)).toBe(false);
      expect(isRequired(undefined)).toBe(false);
    });
  });

  describe('field validators return message or empty string', () => {
    it('validateEmail', () => {
      expect(validateEmail('')).toBe('Email is required');
      expect(validateEmail('bad')).toBe('Invalid email format');
      expect(validateEmail('a@b.co')).toBe('');
    });
    it('validatePassword', () => {
      expect(validatePassword('')).toBe('Password is required');
      expect(validatePassword('short1A')).toBe('Password must be at least 8 characters');
      expect(validatePassword('alllower1')).toBe(
        'Password must contain uppercase, lowercase, and numbers'
      );
      expect(validatePassword('GoodPass1')).toBe('');
    });
    it('validatePhone', () => {
      expect(validatePhone('')).toBe('Phone is required');
      expect(validatePhone('abc')).toBe('Invalid phone number');
      expect(validatePhone('+92 300 1234567')).toBe('');
    });
  });

  describe('validateForm', () => {
    it('collects the first error per field and stops', () => {
      const rules = {
        email: [validateEmail],
        password: [validatePassword],
      };
      const errors = validateForm({ email: 'bad', password: '' }, rules);
      expect(errors).toEqual({ email: 'Invalid email format', password: 'Password is required' });
    });

    it('returns an empty object for a valid form', () => {
      const rules = { email: [validateEmail], password: [validatePassword] };
      expect(validateForm({ email: 'a@b.co', password: 'GoodPass1' }, rules)).toEqual({});
    });
  });
});
