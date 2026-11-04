import { prisma } from '@/lib/prisma';
import { fail, forbidden, notFound, ok, serverError, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

const patchSchema = z.object({ isActive: z.boolean() });

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can change a subscriber');

  const { id } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  try {
    const existing = await prisma.newsletterSubscriber.findUnique({ where: { id } });
    if (!existing) return notFound('Subscriber');

    const subscriber = await prisma.newsletterSubscriber.update({
      where: { id },
      data: { isActive: parsed.data.isActive },
    });

    return ok({ id: subscriber.id, isActive: subscriber.isActive }, 'Subscriber updated');
  } catch {
    return serverError('Could not update the subscriber');
  }
}
