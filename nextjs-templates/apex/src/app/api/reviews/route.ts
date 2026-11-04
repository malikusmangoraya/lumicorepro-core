import { prisma } from '@/lib/prisma';
import { created, fail, ok, serverError, tooMany, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { reviewSchema } from '@/lib/validation';
import { clientIp, rateLimit } from '@/lib/rate-limit';

export const dynamic = 'force-dynamic';

/**
 * GET /api/reviews?vehicle=<slug> | ?product=<slug>
 * Public: approved reviews only, plus the average the page can show.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const vehicle = searchParams.get('vehicle');
  const product = searchParams.get('product');
  if (!vehicle && !product) {
    return fail('TARGET_REQUIRED', 'Pass ?vehicle= or ?product=', 400);
  }

  try {
    const where = {
      status: 'approved',
      ...(vehicle ? { vehicle: { slug: vehicle } } : {}),
      ...(product ? { product: { slug: product } } : {}),
    };

    const [items, aggregate] = await Promise.all([
      prisma.review.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        take: 20,
        select: {
          id: true,
          authorName: true,
          rating: true,
          title: true,
          comment: true,
          verifiedPurchase: true,
          createdAt: true,
        },
      }),
      prisma.review.aggregate({ where, _avg: { rating: true }, _count: { _all: true } }),
    ]);

    return ok({
      items,
      average: aggregate._avg.rating ? Math.round(aggregate._avg.rating * 10) / 10 : null,
      count: aggregate._count._all,
    });
  } catch {
    return serverError('Could not read reviews');
  }
}

/** POST /api/reviews — public and moderated; nothing appears until approved. */
export async function POST(request: Request) {
  const ip = clientIp(request.headers);
  const limit = rateLimit(`reviews:${ip}`, 5, 60 * 60 * 1000);
  if (!limit.allowed) {
    const response = tooMany('Too many reviews from this address. Try again later.');
    response.headers.set('Retry-After', String(limit.retryAfter));
    return response;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = reviewSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());
  const input = parsed.data;

  try {
    let vehicleId: string | null = null;
    let productId: string | null = null;
    let targetTitle: string;

    if (input.vehicleSlug) {
      const vehicle = await prisma.vehicle.findUnique({ where: { slug: input.vehicleSlug } });
      if (!vehicle) return fail('VEHICLE_NOT_FOUND', 'That vehicle does not exist', 404);
      vehicleId = vehicle.id;
      targetTitle = vehicle.title;
    } else {
      const product = await prisma.product.findUnique({ where: { slug: input.productSlug! } });
      if (!product) return fail('PRODUCT_NOT_FOUND', 'That product does not exist', 404);
      productId = product.id;
      targetTitle = product.title;
    }

    const session = await getSession().catch(() => null);

    // A buyer is "verified" when the same email has an order for this item that
    // actually progressed past payment. It is evidence, not a claim.
    const orders = await prisma.order.findMany({
      where: {
        customerEmail: input.authorEmail,
        status: { in: ['paid', 'processing', 'shipped', 'delivered'] },
      },
      select: { items: { select: { title: true } } },
      take: 50,
    });
    const verifiedPurchase = orders.some((order) =>
      order.items.some((item) => item.title === targetTitle),
    );

    const review = await prisma.review.create({
      data: {
        vehicleId,
        productId,
        userId: session?.id ?? null,
        authorName: input.authorName,
        authorEmail: input.authorEmail,
        rating: input.rating,
        title: input.title || null,
        comment: input.comment,
        verifiedPurchase,
        status: 'pending',
      },
      select: { id: true, status: true },
    });

    return created(review, 'Review submitted for moderation');
  } catch {
    return serverError('Could not save the review');
  }
}
