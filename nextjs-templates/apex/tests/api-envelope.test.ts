import { describe, expect, it } from 'vitest';
import { created, fail, notFound, ok, unauthorized, validate } from '@/lib/api';

async function body(response: Response) {
  return (await response.json()) as Record<string, unknown>;
}

describe('api envelope', () => {
  it('wraps success in the documented shape', async () => {
    const response = ok({ hello: 'world' });
    const payload = await body(response);
    expect(response.status).toBe(200);
    expect(payload).toMatchObject({
      success: true,
      status: 200,
      message: 'OK',
      data: { hello: 'world' },
    });
    expect(typeof payload.timestamp).toBe('string');
  });

  it('uses 201 for created', async () => {
    const response = created({ id: 'x' });
    expect(response.status).toBe(201);
    expect(await body(response)).toMatchObject({ success: true, status: 201 });
  });

  it('keeps data null on failure and adds a code', async () => {
    const response = fail('BOOM', 'It broke', 500);
    const payload = await body(response);
    expect(response.status).toBe(500);
    expect(payload).toMatchObject({
      success: false,
      status: 500,
      code: 'BOOM',
      data: null,
    });
  });

  it('maps the common errors to the right status', () => {
    expect(unauthorized().status).toBe(401);
    expect(notFound('Vehicle').status).toBe(404);
    expect(validate({ field: ['bad'] }).status).toBe(422);
  });

  it('includes validation details only when given', async () => {
    expect(await body(validate(undefined))).not.toHaveProperty('details');
    expect(await body(validate({ field: ['bad'] }))).toHaveProperty('details');
  });
});
