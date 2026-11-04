import { prisma } from '@/lib/prisma';
import { fail, ok, serverError, tooMany, unauthorized, validate } from '@/lib/api';
import { setSessionCookies, verifyPassword, type SessionUser } from '@/lib/auth';
import { loginSchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`login:${ip}`, 10, 15 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many sign-in attempts. Try again later.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = loginSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  try {
    const user = await prisma.user.findUnique({ where: { email: parsed.data.email } });

    // One message for "no such user" and "wrong password": distinguishing them
    // turns the endpoint into an account-enumeration oracle.
    if (!user || !user.isActive) {
      return unauthorized('Email or password is incorrect');
    }

    const passwordOk = await verifyPassword(parsed.data.password, user.passwordHash);
    if (!passwordOk) return unauthorized('Email or password is incorrect');

    const sessionUser: SessionUser = {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role === 'admin' ? 'admin' : 'customer',
    };
    await setSessionCookies(sessionUser);

    return ok({ user: sessionUser }, 'Signed in');
  } catch {
    return serverError('Could not sign in');
  }
}
