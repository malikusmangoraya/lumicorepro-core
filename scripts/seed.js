/**
 * Database seeder for development environment
 * Usage: node scripts/seed.js
 */
import mongoose from 'mongoose';
import User from '../models/User.js';
import dotenv from 'dotenv';

dotenv.config({ path: './backend/.env' });

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/lumicorepro';

const seedUsers = [
  {
    name: 'Admin User',
    email: 'admin@lumicorepro.com',
    password: 'admin123',
    role: 'admin',
    isVerified: true,
  },
  {
    name: 'Demo User',
    email: 'demo@example.com',
    password: 'demo123',
    role: 'user',
    isVerified: true,
  },
];

async function seed() {
  try {
    await mongoose.connect(MONGODB_URI);
    console.log('Connected to MongoDB');

    // Clear existing data
    await User.deleteMany({});
    console.log('Cleared existing users');

    // Insert seed data
    await User.insertMany(seedUsers);
    console.log('Inserted seed users');

    console.log('Seeding completed successfully!');
  } catch (error) {
    console.error('Seeding failed:', error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
    console.log('Disconnected from MongoDB');
  }
}

seed();