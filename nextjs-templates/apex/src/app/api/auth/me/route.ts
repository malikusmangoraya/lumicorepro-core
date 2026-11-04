import { getSession } from '@/lib/auth';
import { ok, unauthorized } from '@/lib/api';

export const dynamic = 'force-dynamic';

export async function GET() {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  return ok({ user: session });
}
