const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/lumicore_db',
});

// Helper enforcing parameterized queries ($1, $2...)
const query = (text, params) => {
  return pool.query(text, params);
};

module.exports = {
  pool,
  query,
};
