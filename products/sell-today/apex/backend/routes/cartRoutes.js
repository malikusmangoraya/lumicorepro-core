const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ success: true, items: [], total: 0 });
});

router.post('/add', (req, res) => {
  res.json({
    success: true,
    message: 'Item added to cart',
    productId: req.body.productId,
    quantity: req.body.quantity || 1,
  });
});

module.exports = router;
