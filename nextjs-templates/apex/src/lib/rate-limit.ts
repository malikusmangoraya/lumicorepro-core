/**
 * A tiny in-memory sliding-window limiter.
 *
 * It is deliberately simple: a template runs as a single Node process, and a
 * production deployment behind several instances should swap this for the
 * platform's rate limiter (Vercel Firewall, Upstash, Redis). The point is that
 * an unauthenticated write endpoint has *a* bound from day one.
 */
type Bucket = { hits: number[]; };

const buckets = new Map<string, Bucket>();

export function rateLimit(key: string, limit: number, windowMs: number) {
  const now = Date.now();
  const bucket = buckets.get(key) ?? { hits: [] };
  bucket.hits = bucket.hits.filter((time) => now - time < windowMs);

  if (bucket.hits.length >= limit) {
    buckets.set(key, bucket);
    const retryAfter = Math.ceil((windowMs - (now - bucket.hits[0])) / 1000);
    return { allowed: false as const, retryAfter };
  }

  bucket.hits.push(now);
  buckets.set(key, bucket);

  // Keep the map from growing without bound in a long-running process.
  if (buckets.size > 5000) {
    for (const [k, v] of buckets) {
      if (v.hits.length === 0) buckets.delete(k);
    }
  }

  return { allowed: true as const, retryAfter: 0 };
}

export function clientIp(headers: Headers) {
  return (
    headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    headers.get('x-real-ip') ||
    'unknown'
  );
}
