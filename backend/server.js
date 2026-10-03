import express from 'express';
import compression from 'compression';
import morgan from 'morgan';
import cookieParser from 'cookie-parser';
import { Server } from 'socket.io';
import http from 'http';
import swaggerUi from 'swagger-ui-express';
import swaggerJsdoc from 'swagger-jsdoc';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import path from 'path';
import { corsMiddleware, helmetMiddleware } from './middleware/security.js';
import { requestId } from './middleware/requestId.js';
import { apiLimiter } from './middleware/rateLimit.js';
import { verifyAccessToken } from './middleware/auth.js';
import { assertValidConfig, validateConfig } from './config/env.js';
import connectDB from './config/database.js';
import { connectRedis } from './services/cache/redis.client.js';
import passport from 'passport';
import configureOAuth from './services/oauth.service.js';

dotenv.config();

// ── Fail-fast env validation (always strict in production) ──
try {
  if (process.env.NODE_ENV === 'production') {
    assertValidConfig(process.env);
  } else {
    const { errors } = validateConfig(process.env);
    if (errors.length) {
      logger.warn('Environment check (non-fatal in dev):\n - ' + errors.join('\n - '));
    }
  }
} catch (envErr) {
  logger.error(envErr.message);
  process.exit(1);
}

// ── Sentry — must be initialized before any other imports that could throw ──
import * as Sentry from '@sentry/node';
if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV || 'development',
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1.0,
    integrations: [
      Sentry.httpIntegration(),
      Sentry.expressIntegration(),
    ],
  });
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
import authRoutes from './routes/auth.routes.js';
import userRoutes from './routes/user.routes.js';
import productRoutes from './routes/product.routes.js';
import orderRoutes from './routes/order.routes.js';
import paymentRoutes from './routes/payment.routes.js';
import analyticsRoutes from './routes/analytics.routes.js';
import uploadRoutes from './routes/upload.routes.js';
import searchRoutes from './routes/search.routes.js';
import notificationRoutes from './routes/notification.routes.js';
import healthRoutes from './routes/health.routes.js';
import aiRoutes from './routes/ai.routes.js';
import dashboardRoutes from './routes/dashboard.routes.js';
import auditRoutes from './routes/audit.routes.js';
import cartRoutes from './routes/cart.routes.js';
import businessRoutes from './routes/business.routes.js';
import couponRoutes from './routes/coupon.routes.js';
import wishlistRoutes from './routes/wishlist.routes.js';
import subscriptionRoutes from './routes/subscription.routes.js';
import planRoutes from './routes/plan.routes.js';
import addressRoutes from './routes/address.routes.js';
import orgRoutes from './routes/org.routes.js';
import bookingRoutes from './routes/booking.routes.js';
import playbookRoutes from './routes/playbook.routes.js';
import licenseRoutes from './routes/license.routes.js';
import refundPolicyRoutes from './routes/refund-policy.js';
import aiDisclosureRoutes from './routes/ai-disclosure.js';
import settingsRoutes from './routes/settings.routes.js';
import systemConfig from './services/systemConfig.service.js';
import errorHandler, { notFound } from './middleware/errorHandler.js';
import logger from './utils/logger.js';
import { swaggerOptions } from './config/swagger.js';

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    methods: ['GET', 'POST'],
  },
});

// Middleware
app.use(helmetMiddleware);
app.use(compression());
app.use(corsMiddleware);
app.use(requestId);
app.use(cookieParser());

// OAuth (Passport) — Google / GitHub strategies if configured
app.use(passport.initialize());
configureOAuth();

// ── Stripe webhook MUST receive raw body for signature verification ──
// Register this BEFORE express.json() parses the body globally
app.use('/api/payments/webhook', express.raw({ type: 'application/json' }));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
morgan.token('reqId', (req) => req.id || '');
app.use(morgan(':method :url :status :response-time ms :reqId', { stream: { write: (msg) => logger.info(msg.trim(), { http: true }) } }));
// Uploaded files are user-supplied and may include SVGs, which can carry
// <script>. Serve them with a locked-down CSP + nosniff so a stored SVG cannot
// execute script in our origin (stored-XSS hardening).
app.use(
  '/uploads',
  express.static(path.join(__dirname, 'uploads'), {
    setHeaders: (res) => {
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; sandbox");
      res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
    },
  }),
);

// Rate limiting (Redis-backed, per-route granular; loose global for public reads)
app.use('/api/', apiLimiter);

// Swagger documentation
const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Connect to database
connectDB();

// Warm the runtime SystemConfig cache (DB → Redis → memory). Async, non-blocking;
// if the DB is unreachable the service fails open and still serves requests.
connectRedis().then((ok) => {
  logger.info(ok ? 'Redis connected' : 'Redis unavailable — using in-memory fallback');
  systemConfig.refresh().then(() => {
    logger.info('SystemConfig runtime cache warmed');
  });
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/products', productRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/payments', paymentRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/uploads', uploadRoutes);
app.use('/api/search', searchRoutes);
app.use('/api/notifications', notificationRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/audit', auditRoutes);
app.use('/api/cart', cartRoutes);
app.use('/api/business', businessRoutes);
app.use('/api/coupons', couponRoutes);
app.use('/api/wishlist', wishlistRoutes);
app.use('/api/subscriptions', subscriptionRoutes);
app.use('/api/plans', planRoutes);
app.use('/api/addresses', addressRoutes);
app.use('/api/orgs', orgRoutes);
app.use('/api/bookings', bookingRoutes);
app.use('/api/playbook', playbookRoutes);
app.use('/api/license', licenseRoutes);
app.use('/api/legal/refund-policy', refundPolicyRoutes);
app.use('/api/legal/ai-disclosure', aiDisclosureRoutes);
app.use('/api/settings', settingsRoutes);

// Health check routes
app.use('/api/health', healthRoutes);

// WebSocket for real-time notifications
//
// Security: a socket must prove identity before it is allowed to receive
// anything. The JWT is taken from the handshake (`auth.token`) and verified with
// the SAME secret + algorithm pin the REST API uses (middleware/auth.js →
// verifyAccessToken, HS256). Unauthenticated sockets are rejected, so the
// `connection` handler below only ever runs for a verified user.
const userRoom = (id) => `user:${id}`;
const orgRoom = (orgId) => `org:${orgId}`;

io.use((socket, next) => {
  const token = socket.handshake?.auth?.token;
  if (!token) return next(new Error('Authentication required'));

  try {
    const decoded = verifyAccessToken(token);
    if (!decoded?.id) return next(new Error('Authentication required'));
    socket.user = { id: decoded.id, orgId: decoded.org_id || decoded.orgId || null };
    return next();
  } catch {
    return next(new Error('Authentication failed'));
  }
});

/**
 * Rooms a socket is allowed to address — derived ONLY from its verified token,
 * never from client input. Blocks `broadcast`-style joins to rooms the caller
 * does not own. The bare `String(id)` room is kept because
 * routes/notification.routes.js emits notifications to that legacy room name.
 */
const allowedRoomsFor = (socket) => {
  const rooms = new Set([userRoom(socket.user.id), String(socket.user.id)]);
  if (socket.user.orgId != null) rooms.add(orgRoom(socket.user.orgId));
  return rooms;
};

io.on('connection', (socket) => {
  const allowedRooms = allowedRoomsFor(socket);

  // Forced membership: each socket always gets its own identity rooms.
  allowedRooms.forEach((room) => socket.join(room));
  logger.info(`User connected: ${socket.id} (user ${socket.user.id})`);

  socket.on('join-room', (roomId) => {
    const room = typeof roomId === 'string' ? roomId.trim() : '';
    if (!allowedRooms.has(room)) {
      logger.warn(`Socket ${socket.id} denied join to room "${room}"`);
      return;
    }
    socket.join(room);
    logger.info(`Socket ${socket.id} joined room ${room}`);
  });

  socket.on('leave-room', (roomId) => {
    const room = typeof roomId === 'string' ? roomId.trim() : '';
    const isIdentityRoom = room === userRoom(socket.user.id) || room === String(socket.user.id);
    // Identity rooms stay joined for the socket's lifetime.
    if (allowedRooms.has(room) && !isIdentityRoom) {
      socket.leave(room);
      logger.info(`Socket ${socket.id} left room ${room}`);
    }
  });

  socket.on('disconnect', () => {
    logger.info(`User disconnected: ${socket.id}`);
  });
});

// Make io accessible to routes
app.set('io', io);

// ── Sentry error handler — must be AFTER all routes, BEFORE custom errorHandler ──
if (process.env.SENTRY_DSN) {
  Sentry.setupExpressErrorHandler(app);
}

// 404 handler (standardized)
app.use(notFound);

// Error handling
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  logger.info(`Server running on port ${PORT} in ${process.env.NODE_ENV} mode`);
  logger.info(`API Documentation: http://localhost:${PORT}/api-docs`);
});

// ── Graceful shutdown — close HTTP, websockets, Redis, BullMQ queues ──
let shuttingDown = false;
async function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  logger.info(`Received ${signal} — shutting down gracefully...`);

  const timeout = setTimeout(() => {
    logger.warn('Forced shutdown after 10s timeout');
    process.exit(1);
  }, 10_000);
  timeout.unref();

  server.close(async () => {
    try {
      const { closeQueues } = await import('./services/queue/queue.service.js');
      await closeQueues();
      const { disconnectRedis } = await import('./services/cache/redis.client.js');
      await disconnectRedis();
      logger.info('Shutdown complete');
      process.exit(0);
    } catch (err) {
      logger.error(`Shutdown error: ${err.message}`);
      process.exit(1);
    }
  });

  // Force-exit if connections never drain
  setTimeout(() => process.exit(1), 12_000).unref();
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

export default app;
