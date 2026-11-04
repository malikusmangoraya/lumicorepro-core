const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { sequelize, User, Credit } = require('../models');
const { jwtSecret } = require('../utils/jwtSecret');

const router = express.Router();

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

router.post('/register', async (req, res) => {
  try {
    const name = typeof req.body.name === 'string' ? req.body.name.trim() : '';
    const email = typeof req.body.email === 'string' ? req.body.email.trim().toLowerCase() : '';
    const password = typeof req.body.password === 'string' ? req.body.password : '';

    if (!name || !email || !password) {
      return res.status(400).json({ success: false, message: 'Missing required fields' });
    }
    if (name.length < 2 || name.length > 60) {
      return res.status(422).json({ success: false, code: 'VALIDATION', message: 'Name must be 2-60 characters' });
    }
    if (!EMAIL_RE.test(email) || email.length > 190) {
      return res.status(422).json({ success: false, code: 'VALIDATION', message: 'Please enter a valid email address' });
    }
    if (password.length < 8 || password.length > 72) {
      return res.status(422).json({ success: false, code: 'VALIDATION', message: 'Password must be 8-72 characters' });
    }

    const hashedPassword = await bcrypt.hash(password, 12);
    // Registering is a two-table operation: user + starter credits must be
    // committed together, or a failed credit insert would leave the user row
    // orphaned with 0 balance and no way to retry.
    const t = await sequelize.transaction();
    try {
      const user = await User.create({ name, email, password: hashedPassword }, { transaction: t });
      await Credit.create({ userId: user.id, balance: 50, totalGranted: 50 }, { transaction: t });
      await t.commit();
      const token = jwt.sign({ id: user.id, email: user.email }, jwtSecret, { expiresIn: '7d' });
      return res.status(201).json({ success: true, token, user: { id: user.id, name: user.name, email: user.email } });
    } catch (txErr) {
      await t.rollback().catch(() => {});
      throw txErr;
    }
  } catch (err) {
    console.error(`[ERR register] ${err.name}: ${err.message}${err.errors ? `\n${err.errors.map((e2) => `${e2.path}: ${e2.message}`).join("\n")}` : ""}`);
    if (err.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ success: false, code: 'EMAIL_TAKEN', message: 'Email already registered' });
    }
    return res.status(500).json({ success: false, message: 'Registration failed' });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ where: { email } });
    if (!user) return res.status(401).json({ success: false, message: 'Invalid email or password' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(401).json({ success: false, message: 'Invalid email or password' });

    const token = jwt.sign({ id: user.id, email: user.email }, jwtSecret, { expiresIn: '7d' });
    return res.json({ success: true, token, user: { id: user.id, name: user.name, email: user.email } });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Login failed' });
  }
});

module.exports = router;
