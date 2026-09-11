const express = require('express');
const router = express.Router();

router.post('/checkout', (req, res) => {
  res.json({
    success: true,
    orderId: 'ORD-' + Math.floor(100000 + Math.random() * 900000),
    status: 'processing',
    message: 'Order created successfully'
  });
});

module.exports = router;
