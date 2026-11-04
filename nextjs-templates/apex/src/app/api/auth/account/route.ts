import { prisma } from '@/lib/prisma';
import { ok, serverError, unauthorized } from '@/lib/api';
import { clearSessionCookies, getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic';

/** Deleting the account cascades enquiries' user link, cart, wishlist and addresses. */
export async function DELETE() {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();

  try {
    await prisma.user.delete({ where: { id: session.id } });
    await clearSessionCookies();
    return ok({ deleted: true }, 'Account deleted');
  } catch {
    return serverError('Could not delete the account');
  }
}
