import { prisma } from '@/lib/prisma';
import { created, fail, ok, serverError, tooMany, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { leadSchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

/** GET /api/leads — the signed-in customer's own submissions. */
export async function GET() {
  const session = await getSession().catch(() => null);
  if (!session) return ok({ items: [] });

  try {
    const items = await prisma.inquiry.findMany({
      where: { userId: session.id },
      orderBy: { createdAt: 'desc' },
      select: { id: true, type: true, status: true, message: true, createdAt: true },
      take: 50,
    });
    return ok({ items });
  } catch {
    return serverError('Could not read leads');
  }
}

/**
 * POST /api/leads — one endpoint for every lead type: a general enquiry, a test
 * drive request, a finance application or a trade-in valuation.
 *
 * They all land in the same table because they are the same object to the
 * dealership: a person, a car, and a next action. The type decides which extra
 * fields the UI asked for; those go into `metadata` rather than widening the
 * table with columns only one type uses.
 */
export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`leads:${ip}`, 6, 10 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many submissions from this address. Try again later.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = leadSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());
  const input = parsed.data;

  // A test drive is only useful with a date; a finance request is only useful
  // with an amount. Reject the hollow version rather than storing a lead the
  // team cannot act on.
  if (input.type === 'test_drive' && !input.metadata.date) {
    return fail('DATE_REQUIRED', 'Choose a date for the test drive', 422);
  }
  if (input.type === 'finance' && !input.metadata.deposit) {
    return fail('DEPOSIT_REQUIRED', 'Tell us the deposit you have in mind', 422);
  }
  if (input.type === 'trade_in' && !input.metadata.registration) {
    return fail('REGISTRATION_REQUIRED', 'We need the registration to value the car', 422);
  }

  const session = await getSession().catch(() => null);

  try {
    const existing = await prisma.inquiry.findUnique({
      where: { idempotencyKey: input.idempotencyKey },
    });
    if (existing) {
      return ok({ id: existing.id, status: existing.status }, 'Already received');
    }

    let vehicleId: string | null = null;
    if (input.vehicleSlug) {
      const vehicle = await prisma.vehicle.findUnique({
        where: { slug: input.vehicleSlug },
        select: { id: true },
      });
      if (!vehicle) return fail('VEHICLE_NOT_FOUND', 'That vehicle no longer exists', 404);
      vehicleId = vehicle.id;
    }

    const lead = await prisma.inquiry.create({
      data: {
        type: input.type,
        metadata: JSON.stringify(input.metadata),
        vehicleId,
        userId: session?.id ?? null,
        name: input.name,
        email: input.email,
        phone: input.phone || null,
        message: input.message,
        consentGiven: input.consentGiven,
        consentAt: new Date(),
        idempotencyKey: input.idempotencyKey,
      },
      select: { id: true, type: true, status: true },
    });

    return created(lead, 'Thanks — a specialist will be in touch');
  } catch {
    return serverError('Could not save your request');
  }
}
