const express = require('express');
const { sequelize } = require('../models');
const router = express.Router();

router.get('/', async (_req, res) => {
  let db = 'healthy';
  try {
    await sequelize.query('SELECT 1');
  } catch (_e2) {
    db = 'unreachable';
  }
  const healthy = db === 'healthy';
  return res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'degraded',
    db,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

module.exports = router;
