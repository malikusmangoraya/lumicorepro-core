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
    if (process.env.NODE_ENV === 'development') {
      await sequelize.sync({ alter: true });
    }
  } catch (error) {
    console.error('Database connection failed:', error.message);
  }
};

module.exports = { sequelize, connectDB };
