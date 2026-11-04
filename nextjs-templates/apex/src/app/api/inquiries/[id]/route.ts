import { prisma } from '@/lib/prisma';
import { fail, forbidden, notFound, ok, serverError, unauthorized, validate } from '@/lib/api';
import { getSession } from '@/lib/auth';
import { inquiryUpdateSchema } from '@/lib/validation';

export const dynamic = 'force-dynamic';

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can update an enquiry');

  const { id } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail('INVALID_JSON', 'Request body must be valid JSON', 400);
  }

  const parsed = inquiryUpdateSchema.safeParse(body);
  if (!parsed.success) return validate(parsed.error.flatten());

  if (parsed.data.status === undefined && parsed.data.adminNotes === undefined) {
    return fail('NOTHING_TO_UPDATE', 'Send a status or adminNotes field', 400);
  }

  try {
    const existing = await prisma.inquiry.findUnique({ where: { id } });
    if (!existing) return notFound('Enquiry');

    const inquiry = await prisma.inquiry.update({
      where: { id },
      data: {
        ...(parsed.data.status !== undefined ? { status: parsed.data.status } : {}),
        ...(parsed.data.adminNotes !== undefined ? { adminNotes: parsed.data.adminNotes } : {}),
      },
    });

    return ok(
      { id: inquiry.id, status: inquiry.status, adminNotes: inquiry.adminNotes },
      'Enquiry updated',
    );
  } catch {
    return serverError('Could not update the enquiry');
  }
}
