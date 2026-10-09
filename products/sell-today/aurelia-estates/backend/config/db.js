const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  // DATABASE_URL lives in backend/.env (see backend/.env.example). When it is
  // unset the pool falls back to the standard PGHOST/PGUSER/PGPASSWORD vars.
  connectionString: process.env.DATABASE_URL || undefined,
});

// Helper enforcing parameterized queries ($1, $2...)
const query = (text, params) => {
  return pool.query(text, params);
};

module.exports = {
  pool,
  query,
};
