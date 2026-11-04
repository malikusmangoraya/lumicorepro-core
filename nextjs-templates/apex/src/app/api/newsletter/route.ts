import { prisma } from '@/lib/prisma';
import { created, fail, ok, serverError, tooMany, validate } from '@/lib/api';
import { newsletterSchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`newsletter:${ip}`, 5, 60 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many sign-ups from this address. Try again later.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = newsletterSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  try {
    const existing = await prisma.newsletterSubscriber.findUnique({
      where: { email: parsed.data.email },
    });

    // Re-subscribing is a success, not a "you already exist" error: the visitor
    // asked to be on the list and they are.
    if (existing) {
      if (!existing.isActive) {
        await prisma.newsletterSubscriber.update({
          where: { id: existing.id },
          data: { isActive: true, source: parsed.data.source },
        });
      }
      return ok({ subscribed: true }, 'You are already on the list');
    }

    await prisma.newsletterSubscriber.create({ data: parsed.data });
    return created({ subscribed: true }, 'Subscribed');
  } catch {
    return serverError('Could not save the subscription');
  }
}
