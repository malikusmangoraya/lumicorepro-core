import { prisma } from '@/lib/prisma';
import { ok, serverError } from '@/lib/api';

export const dynamic = 'force-dynamic';

/**
 * Health proves the database, not just the process: a deployment that returns
 * 200 while Postgres is unreachable is a deployment that looks alive and is not.
 */
export async function GET() {
  const started = Date.now();
  try {
    await prisma.$queryRaw`SELECT 1`;
    return ok({
      status: 'healthy',
      db: 'connected',
      uptimeSeconds: Math.round(process.uptime()),
      latencyMs: Date.now() - started,
    });
  } catch {
    const response = serverError('Database is unreachable');
    return new Response(response.body, {
      status: 503,
      headers: response.headers,
    });
  }
}
