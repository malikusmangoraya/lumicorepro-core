const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const authRoutes = require('./routes/auth.routes');
const healthRoutes = require('./routes/health.routes');
const { sequelize } = require('./models');

const app = express();
const PORT = process.env.PORT || 5000;

app.set('trust proxy', 1);
app.use(helmet());

// CORS allow-list: browser Origins may only come from CORS_ORIGINS plus the
// documented defaults. Server-to-server callers cannot send Origin, so both
// localhost development and serverless-to-serverless calls are allowed.
const allowedOrigins = (process.env.CORS_ORIGINS ||
  'http://localhost:5173,https://blogforge-lumicorepro.vercel.app')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.includes(origin)) return callback(null, true);
    return callback(null, false);
  },
  credentials: true,
}));

app.use(compression());
app.use(express.json());

const rateLimitOptions = { standardHeaders: true, legacyHeaders: false };
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
  ...rateLimitOptions,
});
const authLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 20,
  ...rateLimitOptions,
});
const aiLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 30,
  ...rateLimitOptions,
});
app.use(limiter);

app.use('/api/v1/auth', authLimiter, authRoutes);
app.use('/api/v1/health', healthRoutes);

const { errorHandler } = require('./middleware/validate');
app.use('/api/v1/records', require('./routes/records.routes'));
try { app.use('/api/v1/ai', aiLimiter, require('./routes/ai')); } catch (_e) { /* kit absent */ }
app.use('/api/v1/blog', require('./routes/blog.routes'));
app.use(errorHandler);

let initPromise = null;
function initDb() {
  if (!initPromise) initPromise = sequelize.sync();
  return initPromise;
}

if (require.main === module) {
  initDb().then(() => {
    app.listen(PORT, () => {
      console.log(`BlogForge Backend API running on port ${PORT}`);
    });
  }).catch(err => {
    console.error('Database connection failed:', err);
  });
}

module.exports = app;
module.exports.initDb = initDb;
