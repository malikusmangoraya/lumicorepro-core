/**
 * Dead-Letter Queue (DLQ) Handler
 * -------------------------------
 * BullMQ marks jobs failed after max attempts. For permanent failures we push a
 * record to a dedicated DLQ (a separate BullMQ queue named `*:dlq`) where an
 * admin/alerting consumer can inspect or replay them.
 */
import { Queue } from 'bullmq';
import { getRedis } from '../cache/redis.client.js';

const connection = getRedis();
const dlqQueues = new Map();

export function getDLQ(sourceQueueName) {
  const name = `${sourceQueueName}-dlq`;
  if (!dlqQueues.has(name)) {
    dlqQueues.set(name, new Queue(name, {
      connection,
      defaultJobOptions: {
        attempts: 1,
        removeOnComplete: { age: 30 * 24 * 3600 },
        removeOnFail: { age: 90 * 24 * 3600 },
      },
    }));
  }
  return dlqQueues.get(name);
}

/** Push a permanently-failed job into the DLQ with the failure reason. */
export async function sendToDLQ(sourceQueueName, job) {
  const q = getDLQ(sourceQueueName);
  const id = await q.add(`${sourceQueueName}:failed`, {
    sourceQueue: sourceQueueName,
    originalJobId: job.id,
    originalData: job.data,
    attemptedAt: new Date().toISOString(),
    failedReason: String(job.failedReason || 'unknown'),
    attemptsMade: job.attemptsMade,
  });
  return id.id;
}

export async function closeDLQs() {
  await Promise.all([...dlqQueues.values()].map((q) => q.close()));
  dlqQueues.clear();
}

export default { getDLQ, sendToDLQ, closeDLQs };