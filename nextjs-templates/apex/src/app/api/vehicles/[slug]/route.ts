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
import { vehicleUpdateSchema } from '@/lib/validation';
import { parseJson } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const { slug } = await params;

  try {
    const session = await getSession().catch(() => null);
    const vehicle = await prisma.vehicle.findFirst({
      where:
        session?.role === 'admin'
          ? { slug }
          : { slug, status: { in: ['active', 'reserved', 'sold'] } },
    });
    if (!vehicle) return notFound('Vehicle');

    return ok({
      ...vehicle,
      media: parseJson(vehicle.media, []),
      inspectionReferences: parseJson(vehicle.inspectionReferences, []),
    });
  } catch {
    return serverError('Could not read the vehicle');
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can edit a vehicle');

  const { slug } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = vehicleUpdateSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  try {
    const existing = await prisma.vehicle.findUnique({ where: { slug } });
    if (!existing) return notFound('Vehicle');

    // Only the keys the caller actually sent are written: a partial update must
    // never blank a field it did not mention.
    const { media, inspectionReferences, ...rest } = parsed.data;
    const data: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(rest)) {
      if (value !== undefined) data[key] = value;
    }
    if (media !== undefined) data.media = JSON.stringify(media);
    if (inspectionReferences !== undefined) {
      data.inspectionReferences = JSON.stringify(inspectionReferences);
    }

    const vehicle = await prisma.vehicle.update({ where: { slug }, data });
    return ok({ ...vehicle, media: parseJson(vehicle.media, []) }, 'Vehicle updated');
  } catch {
    return serverError('Could not update the vehicle');
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can withdraw a vehicle');

  const { slug } = await params;

  try {
    const existing = await prisma.vehicle.findUnique({ where: { slug } });
    if (!existing) return notFound('Vehicle');

    // Withdraw, never delete: an order or an enquiry may point at this row and
    // a hard delete would take the customer's history with it.
    const vehicle = await prisma.vehicle.update({
      where: { slug },
      data: { status: 'withdrawn' },
    });
    return ok({ slug: vehicle.slug, status: vehicle.status }, 'Vehicle withdrawn');
  } catch {
    return serverError('Could not withdraw the vehicle');
  }
}
