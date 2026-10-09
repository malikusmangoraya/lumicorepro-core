/**
 * Queue System (BullMQ, Redis-backed)
 * -----------------------------------
 * A central set of named queues + job producers. Consumers run in the separate
 * worker.js process so the API process is never blocked by CPU-bound jobs
 * (email, AI generation, image processing, report generation, webhooks).
 * Failed jobs use exponential backoff and land in a dead-letter queue after
 * maxAttempts.
 */
import { Queue } from 'bullmq';
import { getRedis } from '../cache/redis.client.js';

const connection = getRedis();

export const QUEUES = {
  EMAIL: 'lh-email',
  AI_GENERATION: 'lh-ai-generation',
  IMAGE_PROCESSING: 'lh-image-processing',
  REPORT: 'lh-report',
  WEBHOOK_RETRY: 'lh-webhook-retry',
  CART_RECOVERY: 'lh-cart-recovery',
};

const defaults = {
  connection,
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: 'exponential', delay: 2_000 },
    removeOnComplete: { age: 86_400, count: 1000 },
    removeOnFail: { age: 604_800, count: 1000 },
  },
};

const queues = new Map();

export function getQueue(name) {
  if (!queues.has(name)) {
    queues.set(name, new Queue(name, defaults));
  }
  return queues.get(name);
}

/**
 * Enqueue a job. Returns { jobId } for tracking.
 * Falls back to an in-process fire-and-forget dispatch when the queue system is
 * unavailable (e.g. Redis down) so callers never block on queue infra.
 */
export async function enqueue(queueName, payload, opts = {}) {
  if (!connection.isMemory) {
    const q = getQueue(queueName);
    const job = await q.add(
      queueName,
      { ...payload, at: Date.now() },
      {
        attempts: opts.attempts,
        backoff: opts.backoff,
        jobId: opts.jobId,
        delay: opts.delay,
        priority: opts.priority ?? 0,
      }
    );
    return { jobId: job.id, fallback: false };
  }

  // In-memory fallback: dispatch inline (fire-and-forget) with attempts ignored.
  const id = opts.jobId || `${queueName}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  const { runInlineJob } = await import('../queue/inlineJobs.js');
  runInlineJob(queueName, { ...payload, at: Date.now() }).catch(() => {});
  return { jobId: id, fallback: true };
}

/** Convenience producers. */
export const enqueueEmail = (payload, opts) => enqueue(QUEUES.EMAIL, payload, opts);
export const enqueueAiGeneration = (payload, opts) => enqueue(QUEUES.AI_GENERATION, payload, opts);
export const enqueueImageProcessing = (payload, opts) =>
  enqueue(QUEUES.IMAGE_PROCESSING, payload, opts);
export const enqueueReport = (payload, opts) => enqueue(QUEUES.REPORT, payload, opts);
export const enqueueWebhookRetry = (payload, opts) => enqueue(QUEUES.WEBHOOK_RETRY, payload, opts);
export const enqueueCartRecovery = (payload, opts) => enqueue(QUEUES.CART_RECOVERY, payload, opts);

export async function closeQueues() {
  await Promise.all([...queues.values()].map((q) => q.close()));
  queues.clear();
}

export default {
  QUEUES,
  getQueue,
  enqueue,
  enqueueEmail,
  enqueueAiGeneration,
  enqueueImageProcessing,
  enqueueReport,
  enqueueWebhookRetry,
  enqueueCartRecovery,
  closeQueues,
};
