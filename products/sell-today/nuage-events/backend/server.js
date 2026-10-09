/**
 * Nuage Events — API server
 *
 * Serves the REST API, the health probes and the Swagger reference.
 * The route modules in ./routes are ES modules; this entry point stays
 * CommonJS and pulls each one in with a dynamic import(), because a static
 * require() cannot load ESM.
 */
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const compression = require('compression');
const cookieParser = require('cookie-parser');
require('dotenv').config();

const { errorHandler, notFound } = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 5000;
const ROUTES_PREFIX = process.env.API_PREFIX || '/api';

// ── Security ────────────────────────────────────────────────────────────────
app.use(helmet({ crossOriginResourcePolicy: { policy: 'cross-origin' } }));

app.use(
  cors({
    origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : true,
    credentials: true,
  })
);

app.use(
  rateLimit({
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 15 * 60 * 1000,
    max: parseInt(process.env.RATE_LIMIT_MAX, 10) || 300,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests. Please slow down and try again shortly.' },
  })
);

// ── Raw body capture for signed payment webhooks ────────────────────────────
// Stripe, PayPal, Paddle and Lemon Squeezy verify an HMAC over the exact bytes
// they sent. The JSON parser below would replace those bytes with a parsed
// object, so these endpoints are read into a Buffer first and the body parsers
// are then told the body has already been read. Every other route keeps the
// normal JSON path.
const SIGNED_WEBHOOK_PATHS = [
  /\/payment\/webhook$/,
  /\/payment\/paypal\/webhook$/,
  /\/payment\/paddle\/webhook$/,
  /\/webhook\/stripe$/,
  /\/lemonsqueezy\/webhook$/,
];
app.use((req, res, next) => {
  if (req.method !== 'POST' || !SIGNED_WEBHOOK_PATHS.some((pattern) => pattern.test(req.path))) {
    return next();
  }
  const limit = parseInt(process.env.WEBHOOK_BODY_LIMIT, 10) || 1024 * 1024;
  const chunks = [];
  let size = 0;
  let overflow = false;
  req.on('data', (chunk) => {
    size += chunk.length;
    if (size > limit) overflow = true;
    else chunks.push(chunk);
  });
  req.on('end', () => {
    if (overflow) return res.status(413).json({ error: 'Webhook payload too large' });
    req.rawBody = Buffer.concat(chunks);
    req.body = req.rawBody;
    req._body = true; // body-parser: already read, do not parse again
    next();
  });
  req.on('error', next);
});

app.use(express.json({ limit: process.env.JSON_BODY_LIMIT || '2mb' }));
app.use(express.urlencoded({ extended: true, limit: process.env.JSON_BODY_LIMIT || '2mb' }));
app.use(compression());

if (process.env.NODE_ENV !== 'test') {
  app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));
}

// ── Cookie parsing (for httpOnly refresh tokens)
app.use(cookieParser());

// ── Routing ─────────────────────────────────────────────────────────────────
/**
 * Load every `*.routes.js` module and mount it at /api/<name>.
 *
 * Each import is isolated: if one module cannot be evaluated (for example an
 * optional payment SDK is not configured), the rest of the API still serves and
 * the failure is reported clearly instead of taking the process down.
 */
async function mountRoutes() {
  const routesDir = path.join(__dirname, 'routes');
  if (!fs.existsSync(routesDir)) {
    console.warn(`[server] no routes directory at ${routesDir}`);
    return [];
  }

  const files = fs
    .readdirSync(routesDir)
    .filter((f) => f.endsWith('.routes.js') || f === 'auth.routes.js')
    .sort();

  const mounted = [];
  for (const file of files) {
    const name = file.replace('.routes.js', '');
    try {
      const mod = await import(pathToFileURL(path.join(routesDir, file)).href);
      const router = mod.default || mod.router;
      if (typeof router !== 'function') {
        console.warn(`[server] ${file} exported no router; skipped`);
        continue;
      }
      app.use(`${ROUTES_PREFIX}/${name}`, router);
      mounted.push(name);
    } catch (err) {
      console.error(`[server] failed to mount ${file}: ${err.message}`);
    }
  }
  return mounted;
}

// ── Operational endpoints ───────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({
    status: 'OK',
    service: 'nuage-events',
    version: require('./package.json').version,
    environment: process.env.NODE_ENV || 'development',
    uptime: Math.round(process.uptime()),
    timestamp: new Date().toISOString(),
  });
});

app.get('/ready', (_req, res) => res.json({ status: 'ready' }));

// ── API documentation ───────────────────────────────────────────────────────
try {
  const swaggerUi = require('swagger-ui-express');
  const swaggerSpec = require('./config/swagger');
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
} catch (err) {
  console.warn(`[server] API docs disabled: ${err.message}`);
}

// ── Start ───────────────────────────────────────────────────────────────────
/**
 * Bind the port first, then load the routers.
 *
 * Loading a router can take a moment (each is a dynamic import, and a broken
 * optional dependency costs a failed resolution). Binding first means
 * /health and /ready answer immediately, so an orchestrator never marks the
 * container unhealthy just because a feature module is still loading.
 */
async function start() {
  const server = app.listen(PORT, () => {
    console.log(`[server] listening on port ${PORT} (${process.env.NODE_ENV || 'development'})`);
  });

  const shutdown = (signal) => () => {
    console.log(`[server] ${signal} received, closing`);
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(1), 10000).unref();
  };
  process.on('SIGTERM', shutdown('SIGTERM'));
  process.on('SIGINT', shutdown('SIGINT'));

  try {
    const monitoring = await import('./utils/monitoring.js');
    if (monitoring && monitoring.initSentry) await monitoring.initSentry(app);
  } catch (err) {
    console.warn(`[server] monitoring disabled: ${err.message}`);
  }

  const mounted = await mountRoutes();

  // The catch-all handlers go on LAST, after every router. Express matches in
  // registration order, so registering `notFound` before the feature routers
  // would swallow every API request and answer 404 for all of them.
  try {
    const monitoring = await import('./utils/monitoring.js');
    if (monitoring && monitoring.attachSentryErrorHandler) await monitoring.attachSentryErrorHandler(app);
  } catch (err) {
    console.warn(`[server] monitoring error handler disabled: ${err.message}`);
  }
  app.use(notFound);
  app.use(errorHandler);

  console.log(`[server] Nuage Events — mounted ${mounted.length} route module(s): ${mounted.join(', ') || 'none'}`);
}

if (require.main === module) {
  start().catch((err) => {
    console.error(`[server] failed to start: ${err.stack || err.message}`);
    process.exit(1);
  });
}

module.exports = { app, start, mountRoutes };
