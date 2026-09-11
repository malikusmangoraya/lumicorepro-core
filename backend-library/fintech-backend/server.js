const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
app.use(helmet());
app.use(express.json());

const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
app.use('/api/', limiter);
app.use(cors());

app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Fintech & Crypto Express API Server Running' });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Fintech Express API running on port ${PORT}`));
