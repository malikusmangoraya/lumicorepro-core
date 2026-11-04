import { prisma } from '@/lib/prisma';
import { created, fail, ok, serverError, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { inquiryQuerySchema, inquirySchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

/**
 * GET /api/inquiries
 *   default  — the signed-in user's own enquiries
 *   ?scope=all — every enquiry, admin only (the queue behind /admin/inquiries)
 */
export async function GET(request: Request) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();

  const { searchParams } = new URL(request.url);
  const parsed = inquiryQuerySchema.safeParse(Object.fromEntries(searchParams));
  if (!parsed.success) return validate(parsed.error.flatten());

  const { scope, status, page, perPage } = parsed.data;
  if (scope === 'all' && session.role !== 'admin') {
    return unauthorized('Only an admin can read the enquiry queue');
  }

  const where = {
    ...(scope === 'all' ? {} : { userId: session.id }),
    ...(status ? { status } : {}),
  };

  try {
    const [items, total] = await Promise.all([
      prisma.inquiry.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
        select: {
          id: true,
          name: true,
          email: true,
          phone: true,
          message: true,
          status: true,
          adminNotes: true,
          createdAt: true,
          vehicle: { select: { slug: true, title: true } },
          user: { select: { id: true, email: true } },
        },
      }),
      prisma.inquiry.count({ where }),
    ]);

    return ok({ items, total, page, perPage, pages: Math.max(1, Math.ceil(total / perPage)) });
  } catch {
    return serverError('Could not read enquiries');
  }
}

/** POST /api/inquiries — public, rate-limited, idempotent. */
export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`inquiries:${ip}`, 5, 10 * 60 * 1000);
  if (!limit.allowed) {
    const response = fail('RATE_LIMITED', 'Too many enquiries from this address.', 429);
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
