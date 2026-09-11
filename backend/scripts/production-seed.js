/**
 * production-seed.js — Live Preview Data Seeding Engine
 * -----------------------------------------------------
 * Injects 10–15 fully-realized, realistic mockup items into the database based
 * on the buyer's business niche (PROJECT_NICHE env), plus a 30-day analytics
 * graph history so the preview looks like a bustling live business instead of
 * an empty template.
 *
 * Usage:
 *   PROJECT_NICHE=healthcare node backend/scripts/production-seed.js
 *   PROJECT_NICHE=ecommerce  node backend/scripts/production-seed.js
 *   PROJECT_NICHE=fitness     node backend/scripts/production-seed.js
 *   node backend/scripts/production-seed.js --list       # show niches
 *
 * Safe: creates records only; does NOT wipe existing data.
 */
import bcrypt from 'bcryptjs';
import { sequelize } from '../config/database.js';
import User from '../models/User.js';
import Product from '../models/Product.js';
import Review from '../models/Review.js';
import Order from '../models/Order.js';
import Notification from '../models/Notification.js';
import Doctor from '../models/Doctor.js';
import Service from '../models/Service.js';
import Booking from '../models/Booking.js';
import AnalyticsEvent from '../models/AnalyticsEvent.js';
import Plan from '../models/Plan.js';
import Category from '../models/Category.js';
import Coupon from '../models/Coupon.js';

const NICHE_DATA = {
  // ── E-COMMERCE ────────────────────────────────────────────────────────────
  ecommerce: {
    products: [
      { title: 'Aurora Wireless ANC Headphones', slug: 'aurora-anc-headphones', category: 'Audio', price: 179.99, thumbnail: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400', stock: 120, description: 'Over-ear headphones with adaptive noise cancellation, 40h battery and multipoint Bluetooth 5.3.', attributes: { colors: ['Midnight', 'Silver'] } },
      { title: 'Pulse Smartwatch Pro', slug: 'pulse-smartwatch-pro', category: 'Wearables', price: 249.00, thumbnail: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400', stock: 85, description: 'AMOLED display, GPS, heart-rate and SpO2 monitoring, 10-day battery life.', attributes: { colors: ['Graphite', 'Rose Gold'] } },
      { title: 'Nimbus Runners v3', slug: 'nimbus-runners-v3', category: 'Footwear', price: 139.50, thumbnail: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', stock: 210, description: 'Carbon-plated road running shoe with responsive midsole foam.', attributes: { colors: ['Coral', 'Mint'] } },
      { title: 'Vertex Mechanical Keyboard', slug: 'vertex-mech-keyboard', category: 'Accessories', price: 119.00, thumbnail: 'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400', stock: 64, description: 'Hot-swappable 75% mechanical keyboard with per-key RGB and aluminium frame.', attributes: { colors: ['Black', 'White'] } },
      { title: 'LumenSmart LED Lamp', slug: 'lumensmart-led-lamp', category: 'Home', price: 49.99, thumbnail: 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400', stock: 300, description: 'Voice-controlled smart lamp with 16M colors, circadian scheduling and USB-C power.', attributes: { colors: ['White'] } },
      { title: 'Terra Stainless Bottle', slug: 'terra-bottle', category: 'Lifestyle', price: 29.99, thumbnail: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400', stock: 450, description: 'Double-wall insulated 1L bottle — 24h cold / 12h hot.', attributes: { colors: ['Forest', 'Sand'] } },
      { title: 'Nova 4K Drone', slug: 'nova-4k-drone', category: 'Cameras', price: 599.00, thumbnail: 'https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400', stock: 18, description: 'Foldable drone with 4K/60fps gimbal camera and 45-min flight time.', attributes: { colors: ['Grey'] } },
      { title: 'Solar Power Bank 20K', slug: 'solar-power-bank', category: 'Electronics', price: 39.99, thumbnail: 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=400', stock: 150, description: '20000mAh fast-charge power bank with solar panel and dual USB-C.', attributes: { colors: ['Black'] } },
      { title: 'Zen Tea Sampler Box', slug: 'zen-tea-sampler', category: 'Grocery', price: 24.00, thumbnail: 'https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?w=400', stock: 500, description: '12 premium loose-leaf teas from Darjeeling, Earl Grey and matcha.', attributes: {} },
      { title: 'Atlas Backpack 32L', slug: 'atlas-backpack', category: 'Accessories', price: 89.00, thumbnail: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400', stock: 97, description: 'Water-resistant travel backpack with padded 16" laptop slot and anti-theft zip.', attributes: { colors: ['Navy', 'Olive'] } },
      { title: 'EchoBook e-Reader', slug: 'echobook-ereader', category: 'Electronics', price: 129.99, thumbnail: 'https://images.unsplash.com/photo-1544330629-b2281aad4c4d?w=400', stock: 55, description: '6" e-ink reader, 300 PPI, weeks of battery, waterproof IPX8.', attributes: { colors: ['Black'] } },
      { title: 'Lume Perfume Discovery Set', slug: 'lume-perfume-set', category: 'Beauty', price: 54.00, thumbnail: 'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=400', stock: 0, description: 'Five 10ml travel fragrances — oud, citrus, amber, floral, oceanic.', attributes: {} },
    ],
    categoryDefs: ['Audio', 'Wearables', 'Footwear', 'Accessories', 'Home', 'Lifestyle', 'Cameras', 'Electronics', 'Grocery', 'Beauty'],
    nicheLabel: 'E-Commerce',
  },

  // ── HEALTHCARE ────────────────────────────────────────────────────────────
  healthcare: {
    doctors: [
      { name: 'Dr. Sarah Mitchell', slug: 'sarah-mitchell', specialty: 'Cardiology', email: 'sarah.mitchell@clinic.example', experience: 14, rating: 4.9, avatar: 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=300', bio: 'Interventional cardiologist focused on preventive heart care and cardiac imaging.', consultationFee: 200 },
      { name: 'Dr. James Okafor', slug: 'james-okafor', specialty: 'Internal Medicine', email: 'james.okafor@clinic.example', experience: 12, rating: 4.8, avatar: 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=300', bio: 'Board-certified internal medicine physician with a focus on chronic disease management.', consultationFee: 150 },
      { name: 'Dr. Aisha Rahman', slug: 'aisha-rahman', specialty: 'Dermatology', email: 'aisha.rahman@clinic.example', experience: 9, rating: 4.9, avatar: 'https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=300', bio: 'Cosmetic and clinical dermatologist; expert in acne, eczema and image-guided skin checks.', consultationFee: 175 },
      { name: 'Dr. Elena Petrova', slug: 'elena-petrova', specialty: 'Pediatrics', email: 'elena.petrova@clinic.example', experience: 15, rating: 5.0, avatar: 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=300', bio: 'Pediatrician providing compassionate care for newborns through adolescence.', consultationFee: 160 },
      { name: 'Dr. Mateo Alvarez', slug: 'mateo-alvarez', specialty: 'Orthopedics', email: 'mateo.alvarez@clinic.example', experience: 11, rating: 4.7, avatar: 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=300', bio: 'Orthopedic surgeon specializing in sports injuries and arthroscopic surgery.', consultationFee: 220 },
    ],
    services: [
      { name: 'Cardiac Screening', slug: 'cardiac-screening', description: 'Comprehensive heart health screening with ECG and stress test.', category: 'cardiology', duration: 45, price: 200.00, depositRequired: 75 },
      { name: 'Annual Physical Exam', slug: 'annual-physical-exam', description: 'Complete annual health checkup with blood work order.', category: 'general', duration: 60, price: 250.00, depositRequired: 0 },
      { name: 'Dermatology Consultation', slug: 'dermatology-consult', description: 'Skin evaluation and personalized treatment plan.', category: 'dermatology', duration: 30, price: 175.00, depositRequired: 50 },
      { name: 'Pediatric Well-Visit', slug: 'pediatric-well-visit', description: 'Growth monitoring, vaccinations and developmental screening.', category: 'pediatrics', duration: 30, price: 140.00, depositRequired: 0 },
      { name: 'Physiotherapy Session', slug: 'physio-session', description: 'One-on-one rehabilitation and mobility training.', category: 'orthopedics', duration: 45, price: 120.00, depositRequired: 30 },
      { name: 'Telehealth Follow-up', slug: 'telehealth-followup', description: 'Remote video consultation for existing patients.', category: 'general', duration: 20, price: 75.00, depositRequired: 0 },
    ],
    nicheLabel: 'Healthcare',
  },

  // ── FITNESS ───────────────────────────────────────────────────────────────
  fitness: {
    memberships: [
      { name: 'Starter', slug: 'starter', price: 29.00, interval: 'monthly', description: 'Full gym floor access, 6am-10pm, includes 1 guest pass monthly.' },
      { name: 'Pro', slug: 'pro', price: 49.00, interval: 'monthly', description: 'All classes, group HIIT, recovery lounge and 4 guest passes.' },
      { name: 'Elite', slug: 'elite', price: 89.00, interval: 'monthly', description: '24/7 access, sauna & spa, 8 PT sessions/year and nutrition plan.' },
      { name: 'Annual Pro', slug: 'annual-pro', price: 490.00, interval: 'yearly', description: 'Full year Pro access at 2 months free.' },
    ],
    trainers: [
      { name: 'Marcus Reed', slug: 'marcus-reed', specialty: 'Strength & Conditioning', rating: 4.9, image: 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300', bio: 'Former national powerlifter; coaches barbell mastery and competition prep.' },
      { name: 'Lina Kowalski', slug: 'lina-kowalski', specialty: 'CrossFit & HIIT', rating: 4.8, image: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300', bio: 'Level-2 CrossFit coach, WOD designer and kettlebell specialist.' },
      { name: 'Diego Fuentes', slug: 'diego-fuentes', specialty: 'Yoga & Mobility', rating: 5.0, image: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=300', bio: 'RYT-500 instructor blending vinyasa flow with myofascial release.' },
      { name: 'Amara Osei', slug: 'amara-osei', specialty: 'Nutrition Coaching', rating: 4.9, image: 'https://images.unsplash.com/photo-1594381898411-846e7d193883?w=300', bio: 'Registered dietitian building sustainable fat-loss and performance plans.' },
    ],
    nicheLabel: 'Fitness',
  },
};

const PRODUCT_DEFS = NICHE_DATA.ecommerce.products;
const REVIEW_SEEDS = [
  'Exceeded my expectations — incredible quality and value.',
  'Shipping was fast and the product is exactly as described.',
  'Highly recommend. Customer service resolved my query in minutes.',
  'Been using it daily for two weeks — genuinely impressed.',
  'Great purchase, worth every cent. The build feels premium.',
  'Solid product, arrived well-packaged and on time.',
  'Five stars. Best purchase of the year so far.',
  'Works perfectly and the setup was effortless.',
  'Exactly what I needed. Delivered ahead of schedule.',
  'Top quality and the colors look even better in person.',
];

const STATUS_POOL = ['delivered', 'delivered', 'delivered', 'shipped', 'processing', 'delivered', 'cancelled', 'delivered', 'processing', 'delivered'];

const seedEcommerce = async (users, customers) => {
  const [admin, vendor] = users;
  const { categoryDefs } = NICHE_DATA.ecommerce;

  const existingProducts = await Product.count();
  const products = [];
  const defs = PRODUCT_DEFS.slice(0, Math.min(12, existingProducts > 0 ? 12 - existingProducts : 12));
  if (defs.length === 0) return;

  for (const c of categoryDefs) {
    await Category.findOrCreate({ where: { name: c }, defaults: { name: c } });
  }

  for (const def of defs) {
    const [product] = await Product.findOrCreate({
      where: { slug: def.slug },
      defaults: { ...def, vendor_id: vendor.id },
    });
    products.push(product);
  }

  for (let i = 0; i < Math.min(products.length, 10); i++) {
    const p = products[i];
    const cust = customers[i % 2];
    await Review.findOrCreate({
      where: { product_id: p.id, user_id: cust.id },
      defaults: {
        user_id: cust.id,
        product_id: p.id,
        userName: cust.name,
        userAvatar: cust.avatar,
        rating: 4 + (i % 2),
        title: `Great ${(p.category || 'product').toLowerCase()} product`,
        comment: REVIEW_SEEDS[i % REVIEW_SEEDS.length],
        verifiedPurchase: true,
      },
    });
  }

  // 15 orders spread over the last 30 days for realistic graphs
  for (let i = 0; i < 15; i++) {
    const prod = products[i % products.length];
    const cust = customers[i % 2];
    const qty = 1 + (i % 3);
    const itemsPrice = Math.round(parseFloat(prod.price) * qty * 100) / 100;
    const daysAgo = 30 - i * 2;
    const status = STATUS_POOL[i % STATUS_POOL.length];
    await Order.findOrCreate({
      where: { orderNumber: `ORD-PREVIEW-${i + 1}` },
      defaults: {
        user_id: cust.id,
        orderNumber: `ORD-PREVIEW-${i + 1}`,
        items: [{ product_id: prod.id, title: prod.title, price: parseFloat(prod.price), quantity: qty, image: prod.thumbnail }],
        shippingAddress: cust.address,
        billingAddress: cust.address,
        paymentMethod: 'stripe',
        itemsPrice,
        taxPrice: Math.round(itemsPrice * 0.08 * 100) / 100,
        shippingPrice: itemsPrice > 100 ? 0 : 9.99,
        totalPrice: Math.round((itemsPrice * 1.08 + (itemsPrice > 100 ? 0 : 9.99)) * 100) / 100,
        isPaid: status !== 'cancelled',
        paidAt: status !== 'cancelled' ? new Date(Date.now() - daysAgo * 86400000) : null,
        isDelivered: status === 'delivered',
        deliveredAt: status === 'delivered' ? new Date(Date.now() - (daysAgo - 2) * 86400000) : null,
        status,
      },
    });
  }

  return {
    type: 'ecommerce',
    items: products.length,
    orders: 15,
    users: [admin, vendor, ...customers],
  };
};

const seedHealthcare = async (users, customers) => {
  const [admin] = users;
  const { doctors: doctorDefs, services: serviceDefs } = NICHE_DATA.healthcare;

  const doctors = [];
  for (const def of doctorDefs) {
    const [doc] = await Doctor.findOrCreate({ where: { slug: def.slug }, defaults: def });
    doctors.push(doc);
  }

  const services = [];
  for (const def of serviceDefs) {
    const [svc] = await Service.findOrCreate({ where: { slug: def.slug }, defaults: def });
    services.push(svc);
  }

  const times = ['09:00', '10:00', '11:30', '14:00', '09:30', '10:30', '13:00', '15:00'];
  const statuses = ['confirmed', 'confirmed', 'pending', 'completed', 'confirmed', 'cancelled', 'confirmed', 'pending'];
  for (let i = 0; i < 8; i++) {
    const doc = doctors[i % doctors.length];
    const svc = services[i % services.length];
    const u = customers[i % 2];
    const d = new Date();
    d.setDate(d.getDate() + 1 + i);
    await Booking.findOrCreate({
      where: { bookingNumber: `BK-PREVIEW-${i + 1}` },
      defaults: {
        user_id: u.id,
        doctor_id: doc.id,
        service_id: svc.id,
        bookingNumber: `BK-PREVIEW-${i + 1}`,
        date: d.toISOString().slice(0, 10),
        time: times[i],
        duration: svc.duration,
        status: statuses[i],
        reason: i % 2 === 0 ? 'Routine checkup' : 'Follow-up consultation',
        patientInfo: { firstName: u.name.split(' ')[0], lastName: u.name.split(' ')[1] || '', phone: u.phone, email: u.email },
        totalAmount: parseFloat(svc.price),
        depositAmount: parseFloat(svc.depositRequired),
        paymentStatus: i < 4 ? 'deposit_paid' : 'pending',
      },
    });
  }

  // Revenue history — one order-ish event per day for 30 days
  await seedAnalyticsHistory(admin.id, 'healthcare');

  return { type: 'healthcare', doctors: doctors.length, services: services.length, bookings: 8, users: [admin, ...customers] };
};

const seedFitness = async (users, customers) => {
  const [admin] = users;
  const { memberships: membershipDefs, trainers } = NICHE_DATA.fitness;

  for (const [idx, def] of membershipDefs.entries()) {
    const isYear = def.interval === 'yearly';
    await Plan.findOrCreate({
      where: { slug: def.slug },
      defaults: {
        name: def.name,
        slug: def.slug,
        description: def.description,
        amount: def.price,
        currency: 'usd',
        interval: isYear ? 'year' : 'month',
        creditsGrant: isYear ? 12 : 1,
        features: ['Full gym floor access', 'All group classes', 'Member app + booking', 'Guest passes'].slice(0, 3 + idx),
        highlight: def.slug === 'pro',
        isActive: true,
        sortOrder: idx,
      },
    });
  }

  // Trainers live on our fitness templates as static content; seed plans only.
  await seedAnalyticsHistory(admin.id, 'fitness');

  return { type: 'fitness', memberships: membershipDefs.length, trainers: trainers.length, users: [admin, ...customers] };
};

const seedAnalyticsHistory = async (userId, niche) => {
  // 30 days of daily events for dashboard graphs
  for (let i = 0; i < 30; i++) {
    const date = new Date(Date.now() - i * 86400000);
    const traffic = 40 + Math.floor(Math.random() * 220);
    const conversions = niche === 'healthcare' ? 4 + Math.floor(Math.random() * 18) : 3 + Math.floor(Math.random() * 25);
    try {
      await AnalyticsEvent.create({
        user_id: userId,
        eventName: 'daily:stats',
        payload: {
          date: date.toISOString().slice(0, 10),
          visits: traffic,
          conversions,
          revenue: Math.round(conversions * (30 + Math.floor(Math.random() * 170))),
          source: Math.random() > 0.5 ? 'organic' : 'paid',
        },
      });
    } catch {
      /* non-fatal */
    }
  }
};

const seedUsers = async () => {
  const hashedPassword = await bcrypt.hash('Password123!', 10);
  const addr = { street: '100 Silicon Way', city: 'San Francisco', state: 'CA', country: 'USA', zipCode: '94105' };
  const [admin, vendor, customer, customer2] = await Promise.all([
    User.findOrCreate({
      where: { email: 'admin@example.com' },
      defaults: { name: 'Admin User', password: hashedPassword, role: 'admin', phone: '+1 555-0100', address: addr, isVerified: true, isActive: true, betaStatus: 'active' },
    }),
    User.findOrCreate({
      where: { email: 'vendor@example.com' },
      defaults: { name: 'Vendor Store', password: hashedPassword, role: 'vendor', phone: '+1 555-0101', address: { ...addr, street: '200 Market St', city: 'Austin', state: 'TX' }, isVerified: true, isActive: true },
    }),
    User.findOrCreate({
      where: { email: 'user@example.com' },
      defaults: { name: 'Alex Johnson', password: hashedPassword, role: 'user', phone: '+1 555-0102', address: { ...addr, street: '350 5th Ave', city: 'New York', state: 'NY' }, isVerified: true, isActive: true },
    }),
    User.findOrCreate({
      where: { email: 'maria@example.com' },
      defaults: { name: 'Maria Garcia', password: hashedPassword, role: 'user', phone: '+1 555-0103', address: { ...addr, street: '123 Main St', city: 'Los Angeles', state: 'CA' }, isVerified: true, isActive: true },
    }),
  ]);
  const users = [admin[0], vendor[0]];
  const customers = [customer[0], customer2[0]];
  await Notification.findOrCreate({
    where: { title: 'Welcome to LumiCorePro', recipient: customers[0].id },
    defaults: { recipient: customers[0].id, type: 'info', title: 'Welcome to LumiCorePro', message: 'Demo store is seeded and ready to explore.', read: false },
  });
  return { users, customers };
};

const main = async () => {
  const nicheArg = process.argv[2];
  if (nicheArg === '--list') {
    const { logger } = await import('../utils/logger.js');
    logger.info('Available niches: ecommerce, healthcare, fitness');
    process.exit(0);
  }

  const niche = (process.env.PROJECT_NICHE || 'ecommerce').toLowerCase();
  if (!NICHE_DATA[niche]) {
    console.error(`Unsupported niche "${niche}". Use one of: ecommerce, healthcare, fitness`);
    process.exit(1);
  }

  console.log('\n========================================');
  console.log(`PRODUCTION SEED — ${NICHE_DATA[niche].nicheLabel.toUpperCase()}`);
  console.log('========================================');

  await sequelize.authenticate();
  console.log('Database connected.\n');

  const { users, customers } = await seedUsers();
  console.log('✓ Seeded users (admin / vendor / 2 customers)');

  const couponCount = await Coupon.count();
  if (couponCount === 0) {
    await Coupon.bulkCreate([
      { code: 'WELCOME15', type: 'percentage', value: 15, minSubtotal: 20, isActive: true, expiresAt: new Date(Date.now() + 90 * 86400000) },
      { code: 'FREESHIP', type: 'fixed', value: 10, minSubtotal: 50, isActive: true, expiresAt: new Date(Date.now() + 60 * 86400000) },
    ]);
    console.log('✓ Seeded coupons (WELCOME15, FREESHIP)');
  }

  let summary;
  if (niche === 'ecommerce') summary = await seedEcommerce(users, customers);
  else if (niche === 'healthcare') summary = await seedHealthcare(users, customers);
  else summary = await seedFitness(users, customers);

  await seedAnalyticsHistory(users[0].id, niche);

  console.log(`\n✓ Preview data ready for "${NICHE_DATA[niche].nicheLabel}" niche`);
  console.log('────────────────────────');
  console.log('Credentials (all): Password123!');
  console.log('  Admin:  admin@example.com');
  console.log('  Vendor: vendor@example.com');
  console.log('  User:   user@example.com');
  console.log('\nSeed complete.\n');

  await sequelize.close();
  process.exit(0);
};

main().catch(async (err) => {
  console.error('\nError during seeding:', err.message || err);
  if (err.original) console.error('DB error:', err.original.message);
  try { await sequelize.close(); } catch { /* ignore */ }
  process.exit(1);
});