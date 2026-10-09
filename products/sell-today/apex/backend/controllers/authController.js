const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { jwtSecret } = require('../utils/jwtSecret');

exports.register = async (req, res) => {
  try {
    const { email, password, name } = req.body;
    const token = jwt.sign({ email, role: 'user' }, jwtSecret, { expiresIn: '7d' });
    res.status(201).json({
      success: true,
      message: 'User registered successfully',
      token,
      user: { email, name },
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const token = jwt.sign({ email, role: 'user' }, jwtSecret, { expiresIn: '7d' });
    res.json({ success: true, message: 'Login successful', token, user: { email } });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.getProfile = async (req, res) => {
  res.json({ success: true, user: req.user });
};
