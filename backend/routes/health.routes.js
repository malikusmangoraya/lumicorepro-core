import express from 'express';
import os from 'os';
import { sequelize } from '../config/database.js';
import { isRedisAvailable, getRedis } from '../services/cache/redis.client.js';

const router = express.Router();

/**
 * @swagger
 * /api/health:
 *   get:
 *     summary: Basic health check
 *     tags: [Health]
 */
router.get('/', (req, res) => {
  res.json({
    success: true,
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
  });
});

/**
 * @swagger
 * /api/health/detailed:
 *   get:
 *     summary: Detailed system and database health status
 *     tags: [Health]
 */
router.get('/detailed', async (req, res) => {
  let dbStatus;
  let databaseInfo;

  try {
    const isConnected = await sequelize.authenticate();
    dbStatus = isConnected ? 'connected' : 'disconnected';
    databaseInfo = {
      status: dbStatus,
      host: sequelize.config.host || 'unknown',
      name: sequelize.config.database || 'lumicorepro',
    };
  } catch (error) {
    dbStatus = 'disconnected';
    databaseInfo = {
      status: dbStatus,
      host: sequelize.config.host || 'unknown',
      name: sequelize.config.database || 'lumicorepro',
      error: error.message,
    };
  }

  const memoryUsage = process.memoryUsage();
  const systemMemory = {
    total: Math.round(os.totalmem() / (1024 * 1024)) + ' MB',
    free: Math.round(os.freemem() / (1024 * 1024)) + ' MB',
  };

  const processMemory = {
    rss: Math.round(memoryUsage.rss / (1024 * 1024)) + ' MB',
    heapTotal: Math.round(memoryUsage.heapTotal / (1024 * 1024)) + ' MB',
    heapUsed: Math.round(memoryUsage.heapUsed / (1024 * 1024)) + ' MB',
  };

  const isHealthy = dbStatus === 'connected';

  // Redis check
  let redisStatus;
  let redisMode;
  try {
    const client = getRedis();
    redisMode = client?.isMemory ? 'in-memory-fallback' : 'connected';
    redisStatus = isRedisAvailable() ? 'connected' : 'fallback';
  } catch {
    redisStatus = 'unavailable';
    redisMode = 'unavailable';
  }

  res.status(isHealthy ? 200 : 503).json({
    success: isHealthy,
    status: isHealthy ? 'HEALTHY' : 'DEGRADED',
    timestamp: new Date().toISOString(),
    uptimeSeconds: Math.floor(process.uptime()),
    database: databaseInfo,
    redis: { status: redisStatus, mode: redisMode },
    system: {
      platform: process.platform,
      nodeVersion: process.version,
      cpuCount: os.cpus().length,
      loadAvg: os.loadavg(),
      memory: systemMemory,
    },
    process: {
      pid: process.pid,
      memory: processMemory,
    },
  });
});

export default router;
