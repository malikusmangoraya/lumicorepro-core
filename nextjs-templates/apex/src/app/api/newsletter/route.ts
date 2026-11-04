import { prisma } from '@/lib/prisma';
import { forbidden, ok, serverError, unauthorized } from '@/lib/api';
import { getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic';

/** GET /api/newsletter — the subscriber list, admin only. */
export async function GET() {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can read subscribers');

  try {
    const [items, active] = await Promise.all([
      prisma.newsletterSubscriber.findMany({
        orderBy: { createdAt: 'desc' },
        take: 200,
      }),
      prisma.newsletterSubscriber.count({ where: { isActive: true } }),
    ]);
    return ok({ items, total: items.length, active });
  } catch {
    return serverError('Could not read subscribers');
  }
}
