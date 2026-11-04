import { describe, expect, it } from 'vitest';
import { inquirySchema, loginSchema, registerSchema, vehicleQuerySchema } from '@/lib/validation';

describe('registerSchema', () => {
  const valid = { name: 'Avery Admin', email: 'Avery@Example.com', password: 'Passw0rd!' };

  it('accepts a valid registration and lowercases the email', () => {
    const parsed = registerSchema.parse(valid);
    expect(parsed.email).toBe('avery@example.com');
  });

  it('rejects a password without a digit', () => {
    const result = registerSchema.safeParse({ ...valid, password: 'OnlyLetters' });
    expect(result.success).toBe(false);
  });

  it('rejects a password shorter than 8 characters', () => {
    const result = registerSchema.safeParse({ ...valid, password: 'a1' });
    expect(result.success).toBe(false);
  });

  it('rejects a malformed email', () => {
    const result = registerSchema.safeParse({ ...valid, email: 'not-an-email' });
    expect(result.success).toBe(false);
  });
});

describe('loginSchema', () => {
  it('defaults remember to false', () => {
    const parsed = loginSchema.parse({ email: 'a@b.com', password: 'x' });
    expect(parsed.remember).toBe(false);
  });
});

describe('inquirySchema', () => {
  const valid = {
    name: 'Casey Customer',
    email: 'casey@example.com',
    message: 'I would like to arrange a viewing this weekend.',
    consentGiven: true,
    idempotencyKey: 'a-unique-key',
    locale: 'en',
  };

  it('accepts a consented enquiry', () => {
    expect(inquirySchema.safeParse(valid).success).toBe(true);
  });

  it('rejects an enquiry without consent', () => {
    expect(inquirySchema.safeParse({ ...valid, consentGiven: false }).success).toBe(false);
  });

  it('rejects a message shorter than 10 characters', () => {
    expect(inquirySchema.safeParse({ ...valid, message: 'hi' }).success).toBe(false);
  });

  it('rejects a message over 4000 characters', () => {
    expect(inquirySchema.safeParse({ ...valid, message: 'x'.repeat(4001) }).success).toBe(false);
  });
});

describe('vehicleQuerySchema', () => {
  it('coerces numbers from query strings', () => {
    const parsed = vehicleQuerySchema.parse({ page: '2', priceMax: '200000' });
    expect(parsed.page).toBe(2);
    expect(parsed.priceMax).toBe(200000);
  });

  it('rejects an unknown sort', () => {
    expect(vehicleQuerySchema.safeParse({ sort: 'cheapest' }).success).toBe(false);
  });

  it('caps perPage so a caller cannot ask for the whole table', () => {
    expect(vehicleQuerySchema.safeParse({ perPage: '5000' }).success).toBe(false);
  });
});
