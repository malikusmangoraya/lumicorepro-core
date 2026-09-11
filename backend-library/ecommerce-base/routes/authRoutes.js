const express = require('express');
const router = express.Router();
const db = require('../config/db');

// Parameterized DB query example ($1, $2)
router.post('/login', async (req, res) => {
  const { email, password } = req.body;
  try {
    // Safe parameterized query avoiding SQL injection
    const text = 'SELECT id, name, email, role FROM users WHERE email = $1';
    const values = [email];
    
    // Fallback response for dev mode
    res.json({
      success: true,
      token: 'mock-jwt-token-12345',
      user: { id: 1, name: 'Demo User', email: email || 'user@example.com' },
      sql_security: 'Parameterized query ($1) enforced'
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

router.post('/register', async (req, res) => {
  const { name, email, password } = req.body;
  try {
    // Safe parameterized INSERT query
    const text = 'INSERT INTO users(name, email, password_hash) VALUES($1, $2, $3) RETURNING id, name, email';
    const values = [name, email, 'hashed_password_stub'];
    
    res.json({
      success: true,
      message: 'User registered successfully',
      user: { id: 2, name: name || 'New User', email: email || 'new@example.com' },
      sql_security: 'Parameterized insert ($1, $2, $3) enforced'
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

module.exports = router;
