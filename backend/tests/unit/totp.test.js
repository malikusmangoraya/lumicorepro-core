import { describe, it, expect, jest, afterEach } from '@jest/globals';
import {
  generateSecret,
  generateTOTP,
  verifyTOTP,
  buildOTPAuthURI,
} from '../../utils/totp.js';

/**
 * RFC 6238 (TOTP) Appendix B known-answer vectors.
 *
 * The RFC publishes 8-digit codes for the ASCII secret "12345678901234567890",
 * whose base32 form is below. TOTP truncates the dynamic-truncation value with
 * `% 10^6`, so the 6-digit code is the low 6 digits of the published 8-digit one.
 * Using the real vectors means this suite would catch an actual change in the
 * HMAC/dynamic-truncation maths, not just a crash.
 */
const RFC_SECRET = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ';
const RFC_VECTORS = [
  { seconds: 59, code: '287082' },
  { seconds: 1111111109, code: '081804' },
  { seconds: 1111111111, code: '050471' },
  { seconds: 1234567890, code: '005924' },
  { seconds: 2000000000, code: '279037' },
  { seconds: 20000000000, code: '353130' },
];

const nowSeconds = (ms) => Math.floor(ms / 1000);

// counter (time-step) for an absolute unix timestamp in seconds
const stepFor = (seconds) => Math.floor(seconds / 30);

describe('totp - generateTOTP against RFC 6238 vectors', () => {
  it.each(RFC_VECTORS)('produces $code at T=$seconds', ({ seconds, code }) => {
    // counter = floor(T / 30)
    expect(generateTOTP(RFC_SECRET, Math.floor(seconds / 30))).toBe(code);
  });

  it('always returns exactly 6 zero-padded digits', () => {
    for (let counter = 0; counter < 500; counter += 1) {
      expect(generateTOTP(RFC_SECRET, counter)).toMatch(/^\d{6}$/);
    }
  });

  it('is deterministic for a fixed counter', () => {
    expect(generateTOTP(RFC_SECRET, 42)).toBe(generateTOTP(RFC_SECRET, 42));
  });

  it('changes across time steps', () => {
    const codes = new Set();
    for (let counter = 1_000_000; counter < 1_000_050; counter += 1) {
      codes.add(generateTOTP(RFC_SECRET, counter));
    }
    expect(codes.size).toBeGreaterThan(1);
  });
});

describe('totp - generateSecret', () => {
  it('produces a base32 secret of the requested length', () => {
    const secret = generateSecret();
    expect(secret).toHaveLength(32);
    expect(secret).toMatch(/^[A-Z2-7]+$/);
  });

  it('honours a custom length', () => {
    expect(generateSecret(16)).toHaveLength(16);
  });

  it('is not predictable across calls', () => {
    const seen = new Set(Array.from({ length: 200 }, () => generateSecret()));
    expect(seen.size).toBe(200);
  });
});

describe('totp - verifyTOTP', () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  const freezeTo = (seconds) => {
    jest.useFakeTimers();
    jest.setSystemTime(seconds * 1000);
  };

  it('accepts a code generated for the current step', () => {
    freezeTo(1_700_000_000);
    const secret = generateSecret();
    expect(verifyTOTP(secret, generateTOTP(secret))).toBe(true);
  });

  it('accepts a code from the previous step (clock skew)', () => {
    freezeTo(1_700_000_000);
    const secret = generateSecret();
    const previous = generateTOTP(secret, stepFor(1_700_000_000) - 1);
    expect(verifyTOTP(secret, previous)).toBe(true);
  });

  it('accepts a code from the next step (clock skew)', () => {
    freezeTo(1_700_000_000);
    const secret = generateSecret();
    const next = generateTOTP(secret, stepFor(1_700_000_000) + 1);
    expect(verifyTOTP(secret, next)).toBe(true);
  });

  it('rejects a code from outside the +/-1 window', () => {
    freezeTo(1_700_000_000);
    const secret = generateSecret();
    const tooOld = generateTOTP(secret, stepFor(1_700_000_000) - 5);
    expect(verifyTOTP(secret, tooOld)).toBe(false);
  });

  it('rejects a code belonging to a different secret', () => {
    freezeTo(1_700_000_000);
    const secret = generateSecret();
    const foreign = generateTOTP(generateSecret());
    expect(verifyTOTP(secret, foreign)).toBe(false);
  });

  it('rejects empty or missing input instead of throwing', () => {
    expect(verifyTOTP('', '123456')).toBe(false);
    expect(verifyTOTP(generateSecret(), '')).toBe(false);
    expect(verifyTOTP(null, null)).toBe(false);
    expect(verifyTOTP(undefined, undefined)).toBe(false);
  });

  it('rejects a code replayed from an expired step', () => {
    const secret = generateSecret();
    freezeTo(1_700_000_000);
    const code = generateTOTP(secret);
    // move far past the validity window
    jest.setSystemTime(1_700_000_000 * 1000 + 30 * 60 * 1000);
    expect(verifyTOTP(secret, code)).toBe(false);
  });
});

describe('totp - buildOTPAuthURI', () => {
  it('builds an otpauth URI with the expected parameters', () => {
    const uri = buildOTPAuthURI({
      secret: RFC_SECRET,
      accountName: 'user@example.com',
      issuer: 'LumicorePro',
    });
    expect(uri).toContain('otpauth://totp/');
    expect(uri).toContain(`secret=${RFC_SECRET}`);
    expect(uri).toContain('issuer=LumicorePro');
    expect(uri).toContain('algorithm=SHA1');
    expect(uri).toContain('digits=6');
    expect(uri).toContain('period=30');
  });

  it('URL-encodes the issuer:account label', () => {
    const uri = buildOTPAuthURI({
      secret: RFC_SECRET,
      accountName: 'user@example.com',
      issuer: 'My Brand',
    });
    expect(uri).toContain('My%20Brand%3Auser%40example.com');
    expect(uri).not.toContain(' ');
  });
});
