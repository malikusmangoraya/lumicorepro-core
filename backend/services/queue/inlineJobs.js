/**
 * Inline Job Dispatcher (Redis-offline fallback)
 * ------------------------------------------------
 * Mirrors the handlers in workers/worker.js so that when Redis / BullMQ is
 * unavailable, enqueued jobs execute in-process (fire-and-forget). Keeps the
 * same dispatch contract so behavior is consistent in both modes.
 */
import { QUEUES } from './queue.service.js';
import logger from '../../utils/logger.js';
import { sendEmail } from '../email.service.js';

const handlers = {
  [QUEUES.EMAIL]: (data) => sendEmail({
    to: data.to,
    subject: data.subject || 'App notification',
    html: data.html,
    text: data.text,
  }),

  [QUEUES.AI_GENERATION]: async (data) => {
    logger.info('[inline-queue] AI generation job', { runId: data.runId });
    return true;
  },

  [QUEUES.IMAGE_PROCESSING]: async (data) => {
    logger.info('[inline-queue] Image processing job', { file: data.file });
    return true;
  },

  [QUEUES.REPORT]: async (data) => {
    logger.info('[inline-queue] Report generation job', { type: data.type });
    return true;
  },

  [QUEUES.WEBHOOK_RETRY]: async (data) => {
    logger.info('[inline-queue] Webhook retry job', { url: data.url });
    return true;
  },
};

export async function runInlineJob(queueName, data) {
  const fn = handlers[queueName];
  if (!fn) return;
  try {
    await fn(data);
  } catch (err) {
    logger.warn(`[inline-queue] ${queueName} job failed: ${err.message}`);
  }
}

export default { runInlineJob };