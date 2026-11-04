const app = require('../server');

module.exports = async (req, res) => {
  try {
    await app.initDb();
  } catch (err) {
    console.error('Database init failed:', err.message);
    res.status(503).json({ success: false, message: 'Database unavailable' });
    return;
  }
  app(req, res);
};
