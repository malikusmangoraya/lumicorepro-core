import { prisma } from '@/lib/prisma';
import { created, fail, forbidden, ok, serverError, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { vehicleCreateSchema, vehicleQuerySchema } from '@/lib/validation';
import { slugify } from '@/lib/utils';
import { parseJson } from '@/lib/utils';
import { getVehiclesBySlugs } from '@/lib/vehicles';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const parsed = vehicleQuerySchema.safeParse(Object.fromEntries(searchParams));
  if (!parsed.success) return validate(parsed.error.flatten());

  const { q, make, priceMax, sort, page, perPage, slugs } = parsed.data;

  // Explicit slug lists back the saved and compare trays, which live in the
  // browser's storage and therefore cannot be queried by the server.
  if (slugs) {
    const items = await getVehiclesBySlugs(
      slugs.split(',').map((slug) => slug.trim()).filter(Boolean),
    );
    return ok({ items, total: items.length, page: 1, perPage: items.length, pages: 1 });
  }

  const where = {
    status: 'active' as const,
    ...(make ? { make } : {}),
    ...(priceMax ? { price: { lte: priceMax } } : {}),
    ...(q
      ? {
          OR: [
            { title: { contains: q } },
            { make: { contains: q } },
            { model: { contains: q } },
          ],
        }
      : {}),
  };

  const orderBy =
    sort === 'price-asc'
      ? { price: 'asc' as const }
      : sort === 'price-desc'
        ? { price: 'desc' as const }
        : sort === 'mileage-asc'
          ? { mileage: 'asc' as const }
          : { createdAt: 'desc' as const };

  try {
    const [rows, total] = await Promise.all([
      prisma.vehicle.findMany({
        where,
        orderBy,
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      prisma.vehicle.count({ where }),
    ]);

    return ok(
      {
        items: rows.map((row) => ({ ...row, media: parseJson(row.media, []) })),
        total,
        page,
        perPage,
        pages: Math.max(1, Math.ceil(total / perPage)),
      },
      'Vehicles retrieved',
    );
  } catch {
    return serverError('Could not read the inventory');
  }
}

export async function POST(request: Request) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can create a vehicle');

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = vehicleCreateSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  const input = parsed.data;
  const base = slugify(`${input.year}-${input.make}-${input.model}`);
  let slug = base;

  try {
    // Slugs are public URLs, so a collision gets a numeric suffix rather than
    // a database error the caller cannot act on.
    for (let attempt = 2; await prisma.vehicle.findUnique({ where: { slug } }); attempt += 1) {
      slug = `${base}-${attempt}`;
      if (attempt > 50) return fail('SLUG_EXHAUSTED', 'Could not allocate a unique slug', 409);
    }

    const vehicle = await prisma.vehicle.create({
      data: {
        ...input,
        media: JSON.stringify(input.media),
        inspectionReferences: JSON.stringify([]),
        slug,
      },
    });

    return created({ ...vehicle, media: input.media }, 'Vehicle created');
  } catch {
    return serverError('Could not create the vehicle');
  }
}
