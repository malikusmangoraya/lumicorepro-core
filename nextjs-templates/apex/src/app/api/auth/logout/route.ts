import { clearSessionCookies } from '@/lib/auth';
import { ok } from '@/lib/api';

export const dynamic = 'force-dynamic';

export async function POST() {
  await clearSessionCookies();
  return ok({ signedOut: true }, 'Signed out');
}
