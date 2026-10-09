import { Sequelize } from 'sequelize';
import logger from '../utils/logger.js';

const IS_PRODUCTION = process.env.NODE_ENV === 'production';

// SECURITY: a hardcoded connection string with a default password is a real
// credential leak. Outside production we keep a localhost dev default for DX;
// in production DATABASE_URL must be provided explicitly.
const databaseUrl = process.env.DATABASE_URL || (IS_PRODUCTION ? '' : 'postgres://postgres:postgres@localhost:5432/lumicorepro');

if (IS_PRODUCTION && !databaseUrl) {
  throw new Error('DATABASE_URL is required in production (refusing to fall back to a hardcoded dev connection string)');
}

const SLOW_QUERY_THRESHOLD_MS = Number(process.env.SLOW_QUERY_THRESHOLD_MS) || 200;

// ── Read replicas ──────────────────────────────────────────────────────────
// Set DB_REPLICA_URLS (comma-separated) to route SELECTs to read replicas and
// writes to the primary. Sequelize picks a read host per query (round-robin),
// so dashboard/analytics reads stop competing with transactional writes.
// Without the env var, behaviour is identical to the single-node setup.
const replicaUrls = (process.env.DB_REPLICA_URLS || '')
  .split(',')
  .map((url) => url.trim())
  .filter(Boolean);
const replication = replicaUrls.length > 0
  ? { write: databaseUrl, read: replicaUrls }
  : undefined;
if (replication) {
  logger.info(`DB replication enabled: 1 primary + ${replicaUrls.length} read replica(s)`);
}

// TLS: production must verify the server certificate. Set DB_SSL_REJECT_UNAUTHORIZED=false
// only for managed providers that present a CA the app cannot chain to.
const DB_SSL_REJECT_UNAUTHORIZED = (process.env.DB_SSL_REJECT_UNAUTHORIZED || 'true').toLowerCase() === 'true';

// Slow-query flag: log any statement running longer than the threshold
const queryLogger = (sql, timing) => {
  if (timing?.duration && timing.duration > SLOW_QUERY_THRESHOLD_MS) {
    logger.warn(`SLOW QUERY (${timing.duration}ms) > ${SLOW_QUERY_THRESHOLD_MS}ms`, {
      sql: sql.replace(/\s+/g, ' ').trim().slice(0, 500),
      durationMs: timing.duration,
      queryType: 'slow',
    });
  }
};

const sequelize = new Sequelize(replication ? undefined : databaseUrl, {
  dialect: 'postgres',
  ...(replication ? { replication } : {}),
  logging: process.env.NODE_ENV === 'development'
    ? (sql, timing) => {
        if (process.env.LOG_QUERIES === 'true') logger.debug(sql.slice(0, 300));
        if (timing?.duration) queryLogger(sql, timing);
      }
    : queryLogger, // production: still flag slow queries
  pool: {
    max: Number(process.env.DB_POOL_MAX) || 10,
    min: Number(process.env.DB_POOL_MIN) || 0,
    acquire: 30000,
    idle: 10000,
  },
  dialectOptions: {
    // Never disable certificate verification by default — that allows MITM on
    // the production database connection.
    ssl: IS_PRODUCTION ? { rejectUnauthorized: DB_SSL_REJECT_UNAUTHORIZED } : false,
  },
});

const connectDB = async () => {
  try {
    await sequelize.authenticate();
    logger.info(`PostgreSQL Connected: ${sequelize.config.host}`);

    if (process.env.NODE_ENV === 'development') {
      await sequelize.sync({ alter: false });
      logger.info('Database tables synchronized');
    }
    return true;
  } catch (error) {
    logger.warn(`Database connection unavailable: ${error.message}. Continuing without a live DB connection.`);
    return false;
  }
};

export { sequelize };
export default connectDB;