import { prisma } from '@/lib/prisma';
import { forbidden, notFound, ok, serverError, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { reviewModerationSchema } from '@/lib/validation';
import { fail } from '@/lib/api';

export const dynamic = 'force-dynamic';

/** PATCH /api/reviews/[id] — admin moderation. */
export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can moderate a review');

  const { id } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = reviewModerationSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  try {
    const existing = await prisma.review.findUnique({ where: { id } });
    if (!existing) return notFound('Review');

    const review = await prisma.review.update({
      where: { id },
      data: { status: parsed.data.status },
      select: { id: true, status: true },
    });
    return ok(review, 'Review updated');
  } catch {
    return serverError('Could not update the review');
  }
}

/** DELETE /api/reviews/[id] — admin only, for spam that should not exist at all. */
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can delete a review');

  const { id } = await params;
  try {
    const existing = await prisma.review.findUnique({ where: { id } });
    if (!existing) return notFound('Review');
    await prisma.review.delete({ where: { id } });
    return ok({ id }, 'Review deleted');
  } catch {
    return serverError('Could not delete the review');
  }
}
