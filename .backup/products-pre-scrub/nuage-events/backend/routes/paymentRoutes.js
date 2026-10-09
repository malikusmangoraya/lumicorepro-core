const express = require('express');
const router = express.Router();
const db = require('../config/db');

// Create Stripe Payment Intent endpoint
router.post('/create-stripe-intent', async (req, res) => {
  try {
    const { amount, currency = 'usd', orderId } = req.body;
    if (!amount) {
      return res.status(400).json({ error: 'Amount is required' });
    }

    // Standard Stripe PaymentIntent mock/integration response
    const clientSecret = `pi_mock_${Date.now()}_secret_${Math.random().toString(36).substring(7)}`;

    // Log payment attempt in database using parameterized SQL
    if (orderId) {
      await db.query(
        'INSERT INTO payments (order_id, amount, payment_method, status) VALUES ($1, $2, $3, $4)',
        [orderId, amount, 'stripe', 'pending']
      );
    }

    res.json({
      success: true,
      clientSecret,
      message: 'Stripe PaymentIntent created successfully',
    });
  } catch (err) {
    console.error('Stripe Intent Error:', err);
    res.status(500).json({ error: 'Internal payment server error' });
  }
});

// Process PayPal Order endpoint
router.post('/process-paypal', async (req, res) => {
  try {
    const { paypalOrderID, amount, orderId } = req.body;

    if (orderId) {
      await db.query(
        'INSERT INTO payments (order_id, amount, payment_method, status) VALUES ($1, $2, $3, $4)',
        [orderId, amount, 'paypal', 'completed']
      );
    }

    res.json({
      success: true,
      transactionId: `PAYPAL_${Date.now()}`,
      message: 'PayPal payment processed successfully',
    });
  } catch (err) {
    console.error('PayPal Payment Error:', err);
    res.status(500).json({ error: 'Internal payment server error' });
  }
});

module.exports = router;
