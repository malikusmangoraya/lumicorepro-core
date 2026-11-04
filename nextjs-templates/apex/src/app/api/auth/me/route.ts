import { getSession } from '@/lib/auth';
import { ok } from '@/lib/api';

export const dynamic = 'force-dynamic';

/**
 * A session probe, not a protected resource. Answering 401 for an anonymous
 * visitor is correct REST but wrong here: every public page calls this on mount,
 * so a 401 paints a red error in every visitor's console and in every error
 * monitor. "Nobody is signed in" is a successful answer to "who am I".
 */
export async function GET() {
  const session = await getSession().catch(() => null);
  return ok({ user: session });
}
