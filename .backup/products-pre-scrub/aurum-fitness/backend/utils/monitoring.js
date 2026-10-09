/**
 * LumicorePro — Monitoring & Observability helpers
 * Uses optional Sentry integration loaded via dynamic import()
 * so the package is not required for the app to start.
 */
import logger from './logger.js';

let SentryInstance = null;

/**
 * Lazily initialise Sentry. Safe to call multiple times — only runs once.
 */
async function getSentry() {
  if (SentryInstance) return SentryInstance;
  if (!process.env.SENTRY_DSN) return null;

  try {
    const mod = await import('@sentry/node');
    SentryInstance = mod;
    return SentryInstance;
  } catch {
    logger.warn('[monitoring] @sentry/node is not installed — error tracking disabled');
    return null;
  }
}

/**
 * Initialize Sentry at app startup.
 * Call this BEFORE mounting any Express middleware.
 */
export const initSentry = async (app) => {
  if (!process.env.SENTRY_DSN) {
    logger.info('[monitoring] Sentry DSN not configured — error tracking disabled');
    return;
  }

  try {
    const Sentry = await getSentry();
    if (!Sentry) return;

    Sentry.init({
      dsn: process.env.SENTRY_DSN,
      environment: process.env.NODE_ENV || 'development',
      tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || '0.2'),
      beforeSend(event) {
        // Drop low-level events in development
        if (process.env.NODE_ENV === 'development' && event.level !== 'error') {
          return null;
        }
        return event;
      },
    });

    if (app) {
      // Sentry request handler must come before all other middleware
      app.use(Sentry.Handlers.requestHandler());
      app.use(Sentry.Handlers.tracingHandler());
    }

    logger.info('[monitoring] Sentry error tracking initialized');
  } catch (err) {
    logger.warn(`[monitoring] Sentry initialization failed: ${err.message}`);
  }
};

/**
 * Attach Sentry error handler middleware.
 * Must be called AFTER all routes and BEFORE the custom errorHandler.
 */
export const attachSentryErrorHandler = async (app) => {
  try {
    const Sentry = await getSentry();
    if (Sentry && app) {
      app.use(Sentry.Handlers.errorHandler());
    }
  } catch {
    /* noop — Sentry optional */
  }
};

/**
 * Time an async operation and log its duration.
 */
export const measurePerformance = async (operationName, fn) => {
  const start = process.hrtime.bigint();
  try {
    const result = await fn();
    const durationMs = Number(process.hrtime.bigint() - start) / 1e6;
    logger.debug(`[perf] ${operationName} → ${durationMs.toFixed(2)}ms`);
    return result;
  } catch (error) {
    const durationMs = Number(process.hrtime.bigint() - start) / 1e6;
    logger.error(
      `[perf] ${operationName} failed after ${durationMs.toFixed(2)}ms — ${error.message}`
    );
    throw error;
  }
};

/**
 * Capture an exception and forward to Sentry (if configured).
 */
export const captureException = async (error, context = {}) => {
  logger.error(`[exception] ${error.message}`, { stack: error.stack, context });

  const Sentry = await getSentry();
  if (Sentry) {
    Sentry.captureException(error, {
      extra: context,
      tags: { service: 'lumicorepro-backend', env: process.env.NODE_ENV || 'development' },
    });
  }
};

/**
 * Capture a diagnostic message.
 */
export const captureMessage = async (message, level = 'info') => {
  logger[level]?.(`[monitor] ${message}`);
  const Sentry = await getSentry();
  if (Sentry) Sentry.captureMessage(message, level);
};

/**
 * Set user context on Sentry scope (call after auth middleware).
 */
export const setSentryUser = async (user) => {
  const Sentry = await getSentry();
  if (Sentry && user) {
    Sentry.setUser({
      id: String(user.id),
      email: user.email,
      role: user.role,
    });
  }
};
