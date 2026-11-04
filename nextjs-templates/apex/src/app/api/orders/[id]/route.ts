import { prisma } from '@/lib/prisma';
import {
  fail,
  forbidden,
  notFound,
  ok,
  serverError,
  unauthorized,
  validate,
} from '@/lib/api';
import { getSession } from '@/lib/auth';
import { orderUpdateSchema } from '@/lib/validation';
import { canTransition, nextStatuses, requiresTracking } from '@/lib/orders';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();

  const { id } = await params;

  try {
    const order = await prisma.order.findUnique({
      where: { id },
      include: { items: true, payments: true, user: { select: { id: true, name: true, email: true } } },
    });
    if (!order) return notFound('Order');

    // An order belongs to the customer who placed it; everyone else needs to be
    // an admin. Returning someone else's order is an IDOR.
    if (session.role !== 'admin' && order.userId !== session.id) {
      return forbidden('You can only read your own orders');
    }

    return ok(order);
  } catch {
    return serverError('Could not read the order');
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can update an order');

  const { id } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = orderUpdateSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  const { status, carrier, trackingNumber, notes } = parsed.data;
  if ([status, carrier, trackingNumber, notes].every((value) => value === undefined)) {
    return fail('NOTHING_TO_UPDATE', 'Send at least one field to update', 400);
  }

  try {
    const existing = await prisma.order.findUnique({ where: { id } });
    if (!existing) return notFound('Order');

    if (status && status !== existing.status && !canTransition(existing.status, status)) {
      return fail(
        'INVALID_TRANSITION',
        `An order cannot go from ${existing.status} to ${status}. Allowed: ${
          nextStatuses(existing.status).join(', ') || 'none'
        }`,
        409,
      );
    }

    if (status && requiresTracking(status) && !trackingNumber && !existing.trackingNumber) {
      return fail(
        'TRACKING_REQUIRED',
        'Add a tracking number before marking the order shipped or delivered',
        422,
      );
    }

    const order = await prisma.order.update({
      where: { id },
      data: {
        ...(status ? { status } : {}),
        ...(carrier !== undefined ? { carrier } : {}),
        ...(trackingNumber !== undefined ? { trackingNumber } : {}),
        ...(notes !== undefined ? { notes } : {}),
        // Derived flags follow the status rather than being set independently,
        // so the list can never show "paid" next to isPaid: false.
        ...(status === 'paid' || status === 'processing' || status === 'shipped' || status === 'delivered'
          ? { isPaid: true }
          : {}),
        ...(status === 'delivered' ? { isDelivered: true } : {}),
        ...(status === 'refunded' ? { isPaid: false } : {}),
      },
      include: { items: true, payments: true },
    });

    return ok(order, 'Order updated');
  } catch {
    return serverError('Could not update the order');
  }
}
