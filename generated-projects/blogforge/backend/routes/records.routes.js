/** routes/records — live CRUD over PostgreSQL (FK: records.userId -> users.id).
 * Lists are user-scoped via req.user (set by auth). All queries run through
 * Sequelize = parameterized = SQLi-safe; bodies pass validate() = XSS-safe.
 */
const express = require('express');
const { DataTypes } = require('sequelize'); // engine models/index.js exports { sequelize, User } only
const { sequelize } = require('../models');
const { jwtSecret } = require('../utils/jwtSecret');
const { validate } = require('../middleware/validate');

const router = express.Router();

const Record = sequelize.define('Record', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  title: { type: DataTypes.STRING(160), allowNull: false },
  body: { type: DataTypes.TEXT },
  status: { type: DataTypes.ENUM('draft', 'published', 'archived'), defaultValue: 'draft' },
  userId: { type: DataTypes.UUID, allowNull: false },
}, { tableName: 'records', underscored: false });

const RULES = {
  title: { required: true, type: 'string', min: 1, max: 160 },
  body: { type: 'string', max: 10000 },
  status: { type: 'string', max: 20 },
};

function authRequired(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ success: false, message: 'Login required' });
  try {
    const jwt = require('jsonwebtoken');
    req.user = jwt.verify(token, jwtSecret);
    return next();
  } catch (_e) {
    return res.status(401).json({ success: false, message: 'Invalid or expired token' });
  }
}

router.use(authRequired);

router.get('/', async (req, res) => {
  const rows = await Record.findAll({ where: { userId: req.user.id }, order: [['createdAt', 'DESC']] });
  res.json({ success: true, data: rows });
});

router.get('/:id', async (req, res) => {
  const row = await Record.findOne({ where: { id: req.params.id, userId: req.user.id } });
  if (!row) return res.status(404).json({ success: false, message: 'Not found' });
  res.json({ success: true, data: row });
});

router.post('/', validate(RULES), async (req, res, next) => {
  try {
    const status = ['draft', 'published', 'archived'].includes(req.body.status) ? req.body.status : 'draft';
    const row = await Record.create({ title: req.body.title, body: req.body.body || '', status, userId: req.user.id });
    res.status(201).json({ success: true, data: row });
  } catch (e) { next(e); }
});

router.put('/:id', validate(RULES), async (req, res, next) => {
  try {
    const row = await Record.findOne({ where: { id: req.params.id, userId: req.user.id } });
    if (!row) return res.status(404).json({ success: false, message: 'Not found' });
    const patch = {};
    if (req.body.title !== undefined) patch.title = req.body.title;
    if (req.body.body !== undefined) patch.body = req.body.body;
    if (req.body.status && ['draft', 'published', 'archived'].includes(req.body.status)) patch.status = req.body.status;
    await row.update(patch);
    res.json({ success: true, data: row });
  } catch (e) { next(e); }
});

router.delete('/:id', async (req, res, next) => {
  try {
    const n = await Record.destroy({ where: { id: req.params.id, userId: req.user.id } });
    if (!n) return res.status(404).json({ success: false, message: 'Not found' });
    res.json({ success: true, data: { deleted: n } });
  } catch (e) { next(e); }
});

module.exports = router;
