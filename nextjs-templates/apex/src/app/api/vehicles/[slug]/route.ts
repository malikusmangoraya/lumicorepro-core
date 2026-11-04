import { prisma } from '@/lib/prisma';
import { notFound, ok, serverError } from '@/lib/api';
import { parseJson } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const { slug } = await params;

  try {
    const vehicle = await prisma.vehicle.findFirst({
      where: { slug, status: { in: ['active', 'reserved', 'sold'] } },
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
