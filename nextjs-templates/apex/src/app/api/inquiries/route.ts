import { prisma } from '@/lib/prisma';
import { created, fail, ok, serverError, tooMany, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { inquirySchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

/** GET /api/inquiries — the signed-in user's own enquiries. */
export async function GET() {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();

  try {
    const rows = await prisma.inquiry.findMany({
      where: { userId: session.id },
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        status: true,
        message: true,
        createdAt: true,
        vehicle: { select: { slug: true, title: true } },
      },
    });
    return ok(rows);
  } catch {
    return serverError('Could not read your enquiries');
  }
}

/** POST /api/inquiries — public, rate-limited, idempotent. */
export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`inquiries:${ip}`, 5, 10 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many enquiries from this address. Try again in a few minutes.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = inquirySchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  const input = parsed.data;
  const headerKey = request.headers.get('idempotency-key');
  const idempotencyKey = headerKey ?? input.idempotencyKey;

  const session = await getSession().catch(() => null);

  try {
    const existing = await prisma.inquiry.findUnique({ where: { idempotencyKey } });
    if (existing) {
      // A replay is a success: the client's retry did not create a duplicate.
      return ok({ id: existing.id, status: existing.status }, 'Enquiry already received');
    }

    if (input.vehicleId) {
      const vehicle = await prisma.vehicle.findUnique({
        where: { id: input.vehicleId },
        select: { id: true },
      });
      if (!vehicle) return fail('VEHICLE_NOT_FOUND', 'That vehicle no longer exists', 404);
    }

    const inquiry = await prisma.inquiry.create({
      data: {
        vehicleId: input.vehicleId ?? null,
        userId: session?.id ?? null,
        name: input.name,
        email: input.email,
        phone: input.phone || null,
        message: input.message,
        locale: input.locale,
        consentGiven: input.consentGiven,
        consentAt: new Date(),
        idempotencyKey,
      },
    });

    return created({ id: inquiry.id, status: inquiry.status }, 'Enquiry received');
  } catch {
    return serverError('Could not save the enquiry');
  }
}
