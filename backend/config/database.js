import { Sequelize } from 'sequelize';
import logger from '../utils/logger.js';

const databaseUrl = process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/lumicorepro';

const SLOW_QUERY_THRESHOLD_MS = Number(process.env.SLOW_QUERY_THRESHOLD_MS) || 200;

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

const sequelize = new Sequelize(databaseUrl, {
  dialect: 'postgres',
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
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
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