import crypto from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { verifyStripeSignature } from '@/lib/payments';

const SECRET = 'whsec_test_secret';

function sign(body: string, timestamp = Math.floor(Date.now() / 1000), secret = SECRET) {
  const digest = crypto.createHmac('sha256', secret).update(`${timestamp}.${body}`, 'utf8').digest('hex');
  return `t=${timestamp},v1=${digest}`;
}

describe('verifyStripeSignature', () => {
  const body = JSON.stringify({ id: 'evt_1', type: 'checkout.session.completed' });

  it('accepts a signature computed over the raw body', () => {
    expect(verifyStripeSignature(body, sign(body), SECRET)).toBe(true);
  });

  it('rejects a body that changed after signing', () => {
    const header = sign(body);
    expect(verifyStripeSignature(`${body} `, header, SECRET)).toBe(false);
  });

  it('rejects the wrong secret', () => {
    expect(verifyStripeSignature(body, sign(body, undefined, 'other'), SECRET)).toBe(false);
  });

  it('rejects a stale timestamp so a captured event cannot be replayed', () => {
    const old = Math.floor(Date.now() / 1000) - 3600;
    expect(verifyStripeSignature(body, sign(body, old), SECRET)).toBe(false);
  });

  it('fails closed when the secret is missing', () => {
    expect(verifyStripeSignature(body, sign(body), undefined)).toBe(false);
  });

  it('fails closed when the header is missing', () => {
    expect(verifyStripeSignature(body, null, SECRET)).toBe(false);
  });

  it('rejects a malformed header', () => {
    expect(verifyStripeSignature(body, 'garbage', SECRET)).toBe(false);
    expect(verifyStripeSignature(body, 't=abc,v1=def', SECRET)).toBe(false);
  });

  it('is not fooled by a signature of a different length', () => {
    const timestamp = Math.floor(Date.now() / 1000);
    expect(verifyStripeSignature(body, `t=${timestamp},v1=deadbeef`, SECRET)).toBe(false);
  });
});
