/**
 * Socket.IO scaling — Redis adapter.
 *
 * A bare Socket.IO server only delivers to sockets connected to ITS process.
 * The moment a second backend replica (or worker restart) exists, rooms split
 * and notifications go missing. This module attaches the official Redis
 * adapter so rooms/broadcasts work across every replica.
 *
 * Behavior:
 *  - REDIS_DISABLED=true  → standalone (documented single-process mode)
 *  - Adapter missing / Redis unreachable → standalone + loud warn (never crash boot)
 *  - Redis reachable      → clustered
 */
import Redis from 'ioredis';
import logger from '../utils/logger.js';

export function socketMode(env = process.env) {
  if ((env.REDIS_DISABLED || '').toLowerCase() === 'true') return 'standalone';
  return 'clustered';
}

export async function setupSocketScaling(io, env = process.env) {
  if (socketMode(env) === 'standalone') {
    logger.info('Socket.IO: standalone mode (REDIS_DISABLED=true)');
    return { clustered: false, mode: 'standalone' };
  }
  const url = env.REDIS_URL || 'redis://localhost:6379';
  let pub = null;
  let sub = null;
  try {
    // Imported lazily: a static import of this optional package used to abort
    // boot on every deployment that had not installed it — the opposite of the
    // documented fail-open behaviour.
    const { createAdapter } = await import('@socket.io/redis-adapter');
    pub = new Redis(url, { lazyConnect: true, maxRetriesPerRequest: 1, connectTimeout: 2000 });
    sub = pub.duplicate();
    await pub.connect();
    await sub.connect();
    await pub.ping();
    io.adapter(createAdapter(pub, sub));
    logger.info('Socket.IO: clustered mode via Redis adapter');
    return { clustered: true, mode: 'clustered' };
  } catch (err) {
    logger.warn(
      `Socket.IO: clustering unavailable (${err.message}) — running standalone; multi-replica ` +
        `deployments require "@socket.io/redis-adapter" installed and a reachable Redis`,
    );
    try { if (pub) await pub.quit().catch(() => {}); } catch { /* ignore */ }
    try { if (sub) await sub.quit().catch(() => {}); } catch { /* ignore */ }
    return { clustered: false, mode: 'standalone' };
  }
}
