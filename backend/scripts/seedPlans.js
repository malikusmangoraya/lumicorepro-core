/**
 * LumicorePro — Seed Pricing Plans & Credit Packs
 * Usage: node backend/scripts/seedPlans.js
 * Run from project root with backend/.env loaded.
 */
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../.env') });

import { sequelize } from '../config/database.js';
import Plan from '../models/Plan.js';

const PLANS = [
  {
    name: 'Starter',
    slug: 'starter',
    description: 'For exploring what LumicorePro can build.',
    stripeProductId: process.env.STRIPE_PRODUCT_STARTER || '',
    stripePriceId: process.env.STRIPE_PRICE_STARTER || '',
    amount: 9,
    currency: 'usd',
    interval: 'month',
    creditsGrant: 5,
    features: ['5 credits / month', '15-phase AI pipeline', 'Community templates', 'Email support'],
    highlight: false,
    sortOrder: 10,
  },
  {
    name: 'Pro',
    slug: 'pro',
    description: 'For freelancers shipping client-ready projects.',
    stripeProductId: process.env.STRIPE_PRODUCT_PRO || '',
    stripePriceId: process.env.STRIPE_PRICE_PRO || '',
    amount: 29,
    currency: 'usd',
    interval: 'month',
    creditsGrant: 50,
    features: ['50 credits / month', 'Screenshot-to-code (vision)', '10+ industry templates', 'Vercel/Railway deploy configs'],
    highlight: true,
    sortOrder: 20,
  },
  {
    name: 'Agency',
    slug: 'agency',
    description: 'For teams & agencies building at scale.',
    stripeProductId: process.env.STRIPE_PRODUCT_AGENCY || '',
    stripePriceId: process.env.STRIPE_PRICE_AGENCY || '',
    amount: 79,
    currency: 'usd',
    interval: 'month',
    creditsGrant: 200,
    features: ['200 credits / month', 'Multi-user orgs (RBAC)', 'Priority infrastructure', 'Dedicated support'],
    highlight: false,
    sortOrder: 30,
  },
  {
    name: 'Credit Pack — 25',
    slug: 'credit-pack-25',
    description: 'One-time credits for extra generations.',
    stripeProductId: process.env.STRIPE_PRODUCT_CREDITS_25 || '',
    stripePriceId: process.env.STRIPE_PRICE_CREDITS_25 || '',
    amount: 10,
    currency: 'usd',
    interval: 'one_time',
    creditsGrant: 25,
    features: ['25 one-time credits', 'Never expire', 'Any plan'],
    highlight: false,
    sortOrder: 40,
  },
  {
    name: 'Credit Pack — 100',
    slug: 'credit-pack-100',
    description: 'Bigger one-time credit top-up.',
    stripeProductId: process.env.STRIPE_PRODUCT_CREDITS_100 || '',
    stripePriceId: process.env.STRIPE_PRICE_CREDITS_100 || '',
    amount: 35,
    currency: 'usd',
    interval: 'one_time',
    creditsGrant: 100,
    features: ['100 one-time credits', 'Never expire', 'Priority queue'],
    highlight: false,
    sortOrder: 50,
  },
];

const seedPlans = async () => {
  try {
    await sequelize.authenticate();
    await sequelize.sync();
    for (const p of PLANS) {
      const [plan, created] = await Plan.findOrCreate({ where: { slug: p.slug }, defaults: p });
      if (!created) await plan.update(p);
      console.log(`${created ? '✅ Created' : '🔄 Updated'} plan: ${p.slug} ($${p.amount}/${p.interval || 'one-time'})`);
    }
    console.log('Plans seeded.');
    await sequelize.close();
  } catch (err) {
    console.error('Seeding failed:', err.message);
    process.exit(1);
  }
};

seedPlans();