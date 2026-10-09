const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = process.env.DATABASE_URL
  ? new Sequelize(process.env.DATABASE_URL, {
      dialect: 'postgres',
      logging: process.env.NODE_ENV === 'development' ? console.log : false,
      dialectOptions:
        process.env.NODE_ENV === 'production'
          ? {
              ssl: { require: true, rejectUnauthorized: false },
            }
          : {},
    })
  : new Sequelize({
      dialect: 'sqlite',
      storage: './database.sqlite',
      logging: false,
    });

const connectDB = async () => {
  try {
    await sequelize.authenticate();
    console.log('Database connected successfully.');
    // Schema changes go through migrations (npm run migrate). The
    // old `sequelize.sync({ alter: true })` path was removed because
    // it mutated the schema outside version control and could not
    // be applied to a production database.

  } catch (error) {
    console.error('Database connection failed:', error.message);
  }
};

module.exports = { sequelize, connectDB };
