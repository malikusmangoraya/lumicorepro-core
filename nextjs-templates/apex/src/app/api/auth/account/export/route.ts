import { prisma } from '@/lib/prisma';
import { serverError, unauthorized } from '@/lib/api';
import { getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic';

/** GDPR/Zod-style data export: everything we hold, as a JSON download. */
export async function GET() {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();

  try {
    const [user, inquiries, addresses, orders, notifications] = await Promise.all([
      prisma.user.findUnique({
        where: { id: session.id },
        select: {
          id: true,
          email: true,
          name: true,
          role: true,
          phone: true,
          createdAt: true,
        },
      }),
      prisma.inquiry.findMany({ where: { userId: session.id } }),
      prisma.address.findMany({ where: { userId: session.id } }),
      prisma.order.findMany({ where: { userId: session.id } }),
      prisma.notification.findMany({ where: { userId: session.id } }),
    ]);

    const payload = {
      exportedAt: new Date().toISOString(),
      user,
      inquiries,
      addresses,
      orders,
      notifications,
    };

    return new Response(JSON.stringify(payload, null, 2), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename="apex-account-export.json"',
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    return serverError('Could not export your data');
  }
}
