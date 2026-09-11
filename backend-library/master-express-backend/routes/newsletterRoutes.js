const express = require('express');
const router = express.Router();
const { subscribe, unsubscribe } = require('../controllers/newsletterController');

// Public routes
router.post('/subscribe', subscribe);
router.post('/unsubscribe', unsubscribe);

module.exports = router;