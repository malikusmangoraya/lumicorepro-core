const express = require('express');
const router = express.Router();
const controller = require('../controllers/itemsController');

router.get('/', (req, res) => {
  if (controller.getAll) return controller.getAll(req, res);
  res.json({ success: true, message: 'Resource endpoint active' });
});

module.exports = router;
