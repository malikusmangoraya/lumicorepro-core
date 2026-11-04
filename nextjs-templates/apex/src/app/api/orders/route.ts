import { prisma } from '@/lib/prisma';
import { created, fail, forbidden, ok, serverError, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { orderCreateSchema, orderQuerySchema } from '@/lib/validation';
import { calculateTotals } from '@/lib/orders';
import { orderNumber } from '@/lib/utils';

export const dynamic = 'force-dynamic';

/**
 * GET /api/orders
 *   default   — the signed-in customer's own orders
 *   ?scope=all — every order, admin only
 */
export async function GET(request: Request) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();

  const { searchParams } = new URL(request.url);
  const parsed = orderQuerySchema.safeParse(Object.fromEntries(searchParams));
  if (!parsed.success) return validate(parsed.error.flatten());

  const { scope, status, q, page, perPage } = parsed.data;
  if (scope === 'all' && session.role !== 'admin') {
    return unauthorized('Only an admin can read every order');
  }

  const where = {
    ...(scope === 'all' ? {} : { userId: session.id }),
    ...(status ? { status } : {}),
    ...(q
      ? {
          OR: [
            { orderNumber: { contains: q } },
            { customerEmail: { contains: q } },
          ],
        }
      : {}),
  };

  try {
    const [items, total] = await Promise.all([
      prisma.order.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
        include: { items: true },
      }),
      prisma.order.count({ where }),
    ]);

    return ok({ items, total, page, perPage, pages: Math.max(1, Math.ceil(total / perPage)) });
  } catch {
    return serverError('Could not read orders');
  }
}

/** POST /api/orders — admin only: a phone/manual order. */
export async function POST(request: Request) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can create an order');

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = orderCreateSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  const input = parsed.data;

  try {
    let title: string;
    let unitPrice: number;
    let productId: string | null = null;

    if (input.vehicleSlug) {
      const vehicle = await prisma.vehicle.findUnique({ where: { slug: input.vehicleSlug } });
      if (!vehicle) return fail('VEHICLE_NOT_FOUND', 'That vehicle does not exist', 404);
      title = vehicle.title;
      unitPrice = input.unitPrice ?? vehicle.price;
    } else {
      const product = await prisma.product.findUnique({ where: { slug: input.productSlug! } });
      if (!product) return fail('PRODUCT_NOT_FOUND', 'That product does not exist', 404);
      title = product.title;
      unitPrice = input.unitPrice ?? product.price;
      productId = product.id;
    }

    const totals = calculateTotals([{ unitPrice, quantity: input.quantity }], {
      discount: input.discount,
      shipping: input.shipping,
    });

    const customer = await prisma.user.findUnique({ where: { email: input.customerEmail } });

    // The order number is derived from the current count, which can collide
    // when two orders are created at once; retry a few times before giving up.
    let order: Awaited<ReturnType<typeof prisma.order.create>> | null = null;
    for (let attempt = 0; attempt < 5 && !order; attempt += 1) {
      const seq = (await prisma.order.count()) + 1 + attempt;
      try {
        order = await prisma.order.create({
          data: {
            orderNumber: orderNumber(seq),
            userId: customer?.id ?? null,
            customerEmail: input.customerEmail,
            subtotal: totals.subtotal,
            discount: totals.discount,
            tax: totals.tax,
            shipping: totals.shipping,
            total: totals.total,
            status: 'pending',
            notes: input.notes,
            items: {
              create: [
                {
                  productId,
                  title,
                  unitPrice,
                  quantity: input.quantity,
                  lineTotal: Math.round(unitPrice * input.quantity * 100) / 100,
                },
              ],
            },
          },
          include: { items: true },
        });
      } catch (error) {
        const code = (error as { code?: string }).code;
        if (code !== 'P2002' || attempt === 4) throw error;
      }
    }

    if (!order) return serverError('Could not allocate an order number');
    return created(order, 'Order created');
  } catch {
    return serverError('Could not create the order');
  }
}
