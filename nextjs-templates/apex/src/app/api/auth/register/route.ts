import { prisma } from '@/lib/prisma';
import { created, fail, serverError, tooMany, validate } from '@/lib/api';
import { hashPassword, setSessionCookies, type SessionUser } from '@/lib/auth';
import { registerSchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`register:${ip}`, 5, 60 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many accounts created from this address.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = registerSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  try {
    const existing = await prisma.user.findUnique({ where: { email: parsed.data.email } });
    if (existing) {
      return fail('EMAIL_TAKEN', 'An account with that email already exists', 409);
    }

    const user = await prisma.user.create({
      data: {
        email: parsed.data.email,
        name: parsed.data.name,
        passwordHash: await hashPassword(parsed.data.password),
        role: 'customer',
      },
    });

    const sessionUser: SessionUser = {
      id: user.id,
      email: user.email,
      name: user.name,
      role: 'customer',
    };
    await setSessionCookies(sessionUser);

    return created({ user: sessionUser }, 'Account created');
  } catch {
    return serverError('Could not create the account');
  }
}
