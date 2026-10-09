/**
 * Background Worker Process (BullMQ consumers)
 * ---------------------------------------------
 * Run as its own process:  node workers/worker.js
 * Consumes email / AI-generation / image-processing / report / webhook-retry
 * queues so the main API process stays responsive. Failed jobs retry with
 * exponential backoff; those that exhaust attempts are pushed to their DLQ.
 */
import { Worker } from 'bullmq';
import path from 'path';
import { promises as fs } from 'fs';
import { QUEUES } from '../services/queue/queue.service.js';
import { sendToDLQ } from '../services/queue/deadLetter.js';
import { getRedis } from '../services/cache/redis.client.js';
import logger, { withRequestId } from '../utils/logger.js';
import { sendEmail } from '../services/email.service.js';

const connection = getRedis();
const log = withRequestId('worker');

let working = false;

const AI_AGENT_URL = (process.env.AI_AGENT_URL || 'http://localhost:8000').replace(/\/+$/, '');
const UPLOADS_ROOT = path.resolve(process.env.UPLOAD_DIR || path.join(process.cwd(), 'uploads'));

async function callAgent(endpoint, options = {}, timeoutMs = 15_000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${AI_AGENT_URL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      signal: controller.signal,
      ...options,
    });
    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(`Agent request failed (${response.status}): ${body.slice(0, 300)}`);
    }
    return response.json();
  } finally {
    clearTimeout(timer);
  }
}

/** Ensure an input path stays inside the allowed uploads root. */
function safeUploadPath(fileName, jobId) {
  const base = path.resolve(fileName);
  if (!base.startsWith(UPLOADS_ROOT + path.sep)) {
    throw new Error(`Image path outside uploads directory (job ${jobId})`);
  }
  return base;
}

// ── Job handlers (each returns true/false or throws to trigger retry) ──────
const handlers = {
  [QUEUES.EMAIL]: async (job) => {
    const { to, subject, html, text } = job.data;
    log.info(`Sending email to ${to}`, { jobId: job.id, subject });
    const result = await sendEmail({ to, subject, html, text });
    if (!result.sent && result.error) {
      log.warn(`Email to ${to} failed: ${result.error}`);
    }
    return true;
  },

  [QUEUES.AI_GENERATION]: async (job) => {
    const { prompt, provider, language, region } = job.data || {};
    log.info(`AI generation job ${job.id}`, { provider, prompt: (prompt || '').slice(0, 80) });
    const data = await callAgent('/api/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt: prompt || '', provider, language, region }),
    });
    log.info(`AI generation job ${job.id} resolved`, { run_id: data.run_id, status: data.status });
    return true;
  },

  [QUEUES.IMAGE_PROCESSING]: async (job) => {
    const { file, dir } = job.data || {};
    log.info(`Image processing job ${job.id}`, { file, dir });
    if (!file) {
      log.warn(`Image job ${job.id} has no file`, { file, dir });
      return true;
    }

    const sourcePath = safeUploadPath(path.join(dir || '', path.basename(file)), job.id);
    const stat = await fs.stat(sourcePath);
    if (!stat.isFile()) {
      log.warn(`Image job ${job.id}: not a file`, { sourcePath });
      return true;
    }

    const { default: sharp } = await import('sharp');
    const ext = path.extname(sourcePath).toLowerCase();
    const thumbName = `${path.basename(file, ext)}-thumb.webp`;
    const thumbPath = path.join(path.dirname(sourcePath), thumbName);
    await sharp(sourcePath)
      .rotate()
      .resize(job.data?.width || 500, job.data?.height || 500, {
        fit: 'inside',
        withoutEnlargement: true,
      })
      .webp({ quality: job.data?.quality || 80 })
      .toFile(thumbPath);

    log.info(`Image job ${job.id} produced thumbnail`, { thumbPath, bytes: stat.size });
    return true;
  },

  [QUEUES.REPORT]: async (job) => {
    const { email, type = 'daily', period = 'day' } = job.data || {};
    log.info(`Report job ${job.id}`, { email, type, period });
    const { default: Order } = await import('../models/Order.js');
    const { default: User } = await import('../models/User.js');
    const { default: Payment } = await import('../models/Payment.js');
    try {
      const since =
        period === 'week'
          ? new Date(Date.now() - 7 * 864e5)
          : period === 'month'
            ? new Date(Date.now() - 30 * 864e5)
            : new Date(Date.now() - 24 * 3600e3);
      const Op = Order.sequelize.Op;

      const [orders, revenue, users, payments] = await Promise.all([
        Order.count({ where: { createdAt: { [Op.gte]: since } } }),
        Order.sum('totalPrice', { where: { createdAt: { [Op.gte]: since } } }),
        User.count({ where: { createdAt: { [Op.gte]: since } } }),
        Payment.count({ where: { createdAt: { [Op.gte]: since } } }),
      ]);

      const summary = {
        period,
        generatedAt: new Date().toISOString(),
        orders: orders ?? 0,
        revenue: Number(revenue || 0),
        newUsers: users ?? 0,
        payments: payments ?? 0,
      };

      const result = await sendEmail({
        to: email,
        subject: `${process.env.APP_BRAND || 'Your App'} ${type} report (${period})`,
        html:
          `<h2>${process.env.APP_BRAND || 'Your App'} ${type} report</h2><ul>` +
          `<li>Orders: ${summary.orders}</li><li>Revenue: ${summary.revenue}</li>` +
          `<li>New users: ${summary.newUsers}</li><li>Payments: ${summary.payments}</li></ul>` +
          `<p>Generated ${summary.generatedAt}</p>`,
      });
      log.info(`Report job ${job.id} sent`, { email, summary });
      if (!result.sent && result.error) log.warn(`Report email failed: ${result.error}`);
      return true;
    } catch (err) {
      log.warn(`Report job ${job.id} could not compute stats: ${err.message}`);
      return true;
    }
  },

  [QUEUES.WEBHOOK_RETRY]: async (job) => {
    const { gateway = 'stripe', eventId, payload } = job.data || {};
    log.info(`Webhook retry job ${job.id}`, { gateway, eventId });

    const { default: WebhookEvent } = await import('../models/WebhookEvent.js');
    const { handleWebhook } = await import('../services/payment/index.js');

    if (eventId) {
      const record = await WebhookEvent.findOne({ where: { event_id: eventId } });
      if (!record) {
        log.warn(`Webhook retry job ${job.id}: event not found in ledger`, { eventId });
        return true;
      }
      if (record.status === 'processed') {
        log.info(`Webhook retry job ${job.id}: already processed`, { eventId });
        return true;
      }
      await record.update({ status: 'failed' });
      await handleWebhook(record.gateway || gateway, record.payload || {});
      await record.update({ status: 'processed' });
      log.info(`Webhook retry job ${job.id}: processed`, { eventId });
      return true;
    }

    if (!payload) {
      log.warn(`Webhook retry job ${job.id}: no payload or eventId`, job.data);
      return true;
    }
    await handleWebhook(gateway, payload);
    log.info(`Webhook retry job ${job.id}: payload processed`, { gateway });
    return true;
  },

  [QUEUES.CART_RECOVERY]: async (job) => {
    const { recoverCart } = await import('../services/checkout/recovery.service.js');
    const result = await recoverCart(job.data?.cartId);
    log.info(`Cart recovery job ${job.id}`, result);
    return true;
  },
};

async function runWorker() {
  const workers = Object.values(QUEUES).map((qname) => {
    const w = new Worker(
      qname,
      async (job) => {
        const fn = handlers[job.queueName];
        if (!fn) return false;
        try {
          return await fn(job);
        } catch (err) {
          log.warn(`Job ${job.id} failed (attempt ${job.attemptsMade + 1}): ${err.message}`, {
            stack: err.stack,
          });
          throw err; // BullMQ will schedule the next retry attempt
        }
      },
      {
        connection,
        concurrency: 5,
        limiter: { max: 100, duration: 1000 },
      }
    );

    // DLQ: after a job exhausts attempts, move it to the dead-letter queue
    w.on('failed', async (job, err) => {
      if (job && job.attemptsMade >= (job.opts?.attempts || 5)) {
        try {
          await sendToDLQ(qname, {
            ...job,
            failedReason: err?.message,
            attemptsMade: job.attemptsMade,
          });
          log.warn(`Job ${job.id} moved to DLQ ${qname}:dlq`);
        } catch (dlqErr) {
          log.error(`DLQ push failed for ${job.id}: ${dlqErr.message}`);
        }
      }
    });

    return w;
  });

  process.on('SIGTERM', async () => {
    working = true;
    await Promise.all(workers.map((w) => w.close()));
    process.exit(0);
  });
  process.on('SIGINT', async () => {
    working = true;
    await Promise.all(workers.map((w) => w.close()));
    process.exit(0);
  });
}

runWorker().catch((err) => {
  logger.error(`Worker bootstrap failed: ${err.message}`);
  process.exit(1);
});

export default { working };
