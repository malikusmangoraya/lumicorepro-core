/**
 * LumicorePro — Full Production-Grade Database Seeder
 * Seeds 20 products, doctors, services, reviews, orders for demo dashboards.
 * Usage: node backend/scripts/seedFull.js
 */
import dotenv from 'dotenv';
import bcrypt from 'bcryptjs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../.env') });

import { sequelize } from '../config/database.js';
import User from '../models/User.js';
import Product from '../models/Product.js';
import Order from '../models/Order.js';
import Review from '../models/Review.js';
import Notification from '../models/Notification.js';
import Doctor from '../models/Doctor.js';
import Service from '../models/Service.js';
import Booking from '../models/Booking.js';

const UNSPLASH = (id, w = 800) => `https://images.unsplash.com/photo-${id}?w=${w}&auto=format&fit=crop&q=80`;

const productDefs = [
  {
    title: 'LumiCore SoundPro Wireless ANC Headphones',
    description: 'Premium active noise-cancelling over-ear headphones with 40-hour battery life, high-res audio certification, and ultra-plush memory foam earcups.',
    price: 249.99, comparePrice: 299.99, discountPercentage: 17,
    sku: 'LUMI-AUD-001', stock: 45, category: 'Audio',
    tags: ['headphones', 'anc', 'wireless', 'bluetooth'],
    images: [UNSPLASH('1505740420928-5e560c06d30e'), UNSPLASH('1484704849700-f032a568e944')],
    thumbnail: UNSPLASH('1505740420928-5e560c06d30e', 400),
    rating: 4.8, reviewCount: 38,
    attributes: { colors: ['Midnight Black', 'Platinum Silver', 'Navy Blue'], brand: 'LumiCore Audio' },
    isFeatured: true,
  },
  {
    title: 'UltraSync Smart Watch Series X',
    description: 'Next-generation smartwatch featuring AMOLED display, ECG monitoring, SpO2 sensor, built-in GPS, and 7-day battery life.',
    price: 199.99, comparePrice: 249.99, discountPercentage: 20,
    sku: 'LUMI-WCH-002', stock: 60, category: 'Wearables',
    tags: ['smartwatch', 'fitness', 'gps', 'health'],
    images: [UNSPLASH('1523275335684-37898b6baf30')],
    thumbnail: UNSPLASH('1523275335684-37898b6baf30', 400),
    rating: 4.9, reviewCount: 52,
    attributes: { colors: ['Space Gray', 'Rose Gold', 'Silver'], sizes: ['40mm', '44mm'], brand: 'UltraSync' },
    isFeatured: true,
  },
  {
    title: 'ProMech RGB Mechanical Keyboard',
    description: 'Customizable hot-swappable mechanical keyboard with per-key RGB lighting, PBT double-shot keycaps, and durable aluminum chassis.',
    price: 129.99, comparePrice: 159.99, discountPercentage: 19,
    sku: 'LUMI-KEY-003', stock: 30, category: 'Accessories',
    tags: ['keyboard', 'gaming', 'rgb', 'mechanical'],
    images: [UNSPLASH('1587829741301-dc798b83add3')],
    thumbnail: UNSPLASH('1587829741301-dc798b83add3', 400),
    rating: 4.7, reviewCount: 24,
    attributes: { colors: ['Chalk White', 'Matte Black'], brand: 'ProMech' },
    isFeatured: true,
  },
  {
    title: 'ErgoLift Dual-Motor Standing Desk',
    description: 'Heavy-duty electric height-adjustable desk with memory presets, solid oak tabletop, integrated cable management, and anti-collision sensor.',
    price: 499.99, comparePrice: 599.99, discountPercentage: 16,
    sku: 'LUMI-DSK-004', stock: 15, category: 'Home Office',
    tags: ['desk', 'standing desk', 'ergonomic', 'furniture'],
    images: [UNSPLASH('1518455027359-f3f8164ba6bd')],
    thumbnail: UNSPLASH('1518455027359-f3f8164ba6bd', 400),
    rating: 4.9, reviewCount: 19,
    attributes: { colors: ['Walnut', 'Natural Oak'], sizes: ['48x30', '60x30'], brand: 'ErgoLift' },
    isFeatured: true,
  },
  {
    title: 'AeroAir 4K Ultra HD Drone',
    description: 'Compact foldable camera drone with 3-axis gimbal, 4K 60fps HDR video, obstacle avoidance, and 34-minute flight time.',
    price: 349.99, comparePrice: 429.99, discountPercentage: 18,
    sku: 'LUMI-DRN-005', stock: 22, category: 'Electronics',
    tags: ['drone', 'camera', '4k', 'photography'],
    images: [UNSPLASH('1508614589041-895b88991e3e')],
    thumbnail: UNSPLASH('1508614589041-895b88991e3e', 400),
    rating: 4.6, reviewCount: 14,
    attributes: { colors: ['Arctic White', 'Carbon Gray'], brand: 'AeroAir' },
    isFeatured: false,
  },
  {
    title: 'PureSound Hi-Fi Bluetooth Speaker',
    description: '360-degree immersive sound with deep bass reflex, IPX7 waterproof rating, and 24 hours of party playtime.',
    price: 79.99, comparePrice: 99.99, discountPercentage: 20,
    sku: 'LUMI-SPK-006', stock: 80, category: 'Audio',
    tags: ['speaker', 'bluetooth', 'waterproof', 'portable'],
    images: [UNSPLASH('1608043152269-423dbba4e7e1')],
    thumbnail: UNSPLASH('1608043152269-423dbba4e7e1', 400),
    rating: 4.5, reviewCount: 42,
    attributes: { colors: ['Forest Green', 'Charcoal', 'Coral Red'], brand: 'PureSound' },
    isFeatured: false,
  },
  {
    title: 'ProShot 50mm f/1.4 Portrait Lens',
    description: 'Professional-grade portrait lens with ultra-fast f/1.4 aperture, nano-coated glass elements, silent STM motor, and weather-sealed body.',
    price: 449.99, comparePrice: 549.99, discountPercentage: 18,
    sku: 'CAM-LNS-007', stock: 18, category: 'Photography',
    tags: ['lens', 'portrait', '50mm', 'photography'],
    images: [UNSPLASH('1516035069371-29a1b244cc32')],
    thumbnail: UNSPLASH('1516035069371-29a1b244cc32', 400),
    rating: 4.8, reviewCount: 31,
    attributes: { mount: ['Canon RF', 'Sony E', 'Nikon Z'], brand: 'ProShot' },
    isFeatured: true,
  },
  {
    title: 'ZenMat Premium Yoga Mat (6mm)',
    description: 'Eco-friendly TPE yoga mat with alignment marks, non-slip dual texture, carrying strap, and antimicrobial surface.',
    price: 59.99, comparePrice: 79.99, discountPercentage: 25,
    sku: 'FIT-MAT-008', stock: 120, category: 'Fitness',
    tags: ['yoga', 'mat', 'fitness', 'eco-friendly'],
    images: [UNSPLASH('1601925260367-aeac040972dd')],
    thumbnail: UNSPLASH('1601925260367-aeac040972dd', 400),
    rating: 4.7, reviewCount: 87,
    attributes: { colors: ['Sage Green', 'Ocean Blue', 'Midnight Purple'], brand: 'ZenMat' },
    isFeatured: false,
  },
  {
    title: 'CloudWalk Ultra Running Shoes',
    description: 'Lightweight carbon-plate running shoes with responsive ZoomX foam, breathable Flyknit upper, and 8mm drop.',
    price: 179.99, comparePrice: 219.99, discountPercentage: 18,
    sku: 'SHO-RUN-009', stock: 40, category: 'Footwear',
    tags: ['running', 'shoes', 'carbon plate', 'marathon'],
    images: [UNSPLASH('1542291026-7eec264c27ff')],
    thumbnail: UNSPLASH('1542291026-7eec264c27ff', 400),
    rating: 4.6, reviewCount: 56,
    attributes: { sizes: ['8', '9', '10', '11', '12'], colors: ['Volt Green', 'Pure Black', 'Summit White'], brand: 'CloudWalk' },
    isFeatured: true,
  },
  {
    title: 'AuraGlow LED Desk Lamp',
    description: 'Wireless charging desk lamp with 5 color temperatures, 10 brightness levels, USB-C port, and touch controls.',
    price: 69.99, comparePrice: 89.99, discountPercentage: 22,
    sku: 'LMP-LED-010', stock: 55, category: 'Home Office',
    tags: ['lamp', 'desk', 'led', 'wireless charging'],
    images: [UNSPLASH('1507473885765-e6ed057ab382')],
    thumbnail: UNSPLASH('1507473885765-e6ed057ab382', 400),
    rating: 4.4, reviewCount: 33,
    attributes: { colors: ['Matte White', 'Space Gray'], brand: 'AuraGlow' },
    isFeatured: false,
  },
  {
    title: 'FitTrack Pro Body Composition Scale',
    description: 'Smart scale measuring 13 body metrics including body fat, muscle mass, BMI, and bone density via BIA sensors.',
    price: 49.99, comparePrice: 69.99, discountPercentage: 29,
    sku: 'FIT-SCA-011', stock: 75, category: 'Fitness',
    tags: ['scale', 'fitness', 'health', 'smart'],
    images: [UNSPLASH('1576671081837-49000212a370')],
    thumbnail: UNSPLASH('1576671081837-49000212a370', 400),
    rating: 4.3, reviewCount: 64,
    attributes: { colors: ['Black', 'White'], brand: 'FitTrack' },
    isFeatured: false,
  },
  {
    title: 'LumiBook Pro 16" Laptop',
    description: 'Ultra-thin 16-inch laptop with M3 chip, 16GB unified memory, 512GB SSD, Liquid Retina XDR display, and 22-hour battery.',
    price: 1299.99, comparePrice: 1499.99, discountPercentage: 13,
    sku: 'LAP-PRO-012', stock: 12, category: 'Electronics',
    tags: ['laptop', 'ultrabook', 'professional', 'apple'],
    images: [UNSPLASH('1496181133206-60e9b6808b24')],
    thumbnail: UNSPLASH('1496181133206-60e9b6808b24', 400),
    rating: 4.9, reviewCount: 98,
    attributes: { colors: ['Space Black', 'Silver'], specs: ['16GB/512GB', '24GB/1TB'], brand: 'LumiBook' },
    isFeatured: true,
  },
  {
    title: 'SonicWave Wireless Earbuds Pro',
    description: 'True wireless earbuds with active noise cancellation, spatial audio, IPX5 rating, and 30-hour total battery.',
    price: 129.99, comparePrice: 159.99, discountPercentage: 19,
    sku: 'AUD-EBD-013', stock: 90, category: 'Audio',
    tags: ['earbuds', 'wireless', 'anc', 'bluetooth'],
    images: [UNSPLASH('1590658268037-6bf12f032f55')],
    thumbnail: UNSPLASH('1590658268037-6bf12f032f55', 400),
    rating: 4.5, reviewCount: 72,
    attributes: { colors: ['Pearl White', 'Obsidian Black', 'Navy'], brand: 'SonicWave' },
    isFeatured: false,
  },
  {
    title: 'TerraSeed Smart Indoor Garden',
    description: 'Automated hydroponic garden with full-spectrum LED grow lights, water pump, and mobile app control for herbs and greens.',
    price: 149.99, comparePrice: 199.99, discountPercentage: 25,
    sku: 'GDN-PLN-014', stock: 25, category: 'Home & Garden',
    tags: ['garden', 'hydroponic', 'smart', 'indoor'],
    images: [UNSPLASH('1416879595882-3373a0480b5b')],
    thumbnail: UNSPLASH('1416879595882-3373a0480b5b', 400),
    rating: 4.4, reviewCount: 28,
    attributes: { colors: ['White', 'Wood'], brand: 'TerraSeed' },
    isFeatured: false,
  },
  {
    title: 'AirPurify HEPA Tower Purifier',
    description: 'Large-room HEPA H13 air purifier with real-time PM2.5 display, whisper-quiet mode, and app control for rooms up to 1200 sq ft.',
    price: 199.99, comparePrice: 279.99, discountPercentage: 29,
    sku: 'HME-PUR-015', stock: 35, category: 'Home & Garden',
    tags: ['air purifier', 'hepa', 'home', 'health'],
    images: [UNSPLASH('1585771724684-38269d6639fd')],
    thumbnail: UNSPLASH('1585771724684-38269d6639fd', 400),
    rating: 4.7, reviewCount: 41,
    attributes: { colors: ['Pearl White', 'Matte Black'], brand: 'AirPurify' },
    isFeatured: false,
  },
  {
    title: 'TitanGrip Adjustable Dumbbell Set',
    description: 'Quick-adjust 5-52.5 lb dumbbell pair with ergonomic grip, 15 weight settings, and compact storage tray.',
    price: 349.99, comparePrice: 449.99, discountPercentage: 22,
    sku: 'FIT-DBL-016', stock: 20, category: 'Fitness',
    tags: ['dumbbells', 'fitness', 'home gym', 'strength'],
    images: [UNSPLASH('1534438327276-14e5300c3a48')],
    thumbnail: UNSPLASH('1534438327276-14e5300c3a48', 400),
    rating: 4.8, reviewCount: 35,
    attributes: { colors: ['Black/Chrome'], brand: 'TitanGrip' },
    isFeatured: true,
  },
  {
    title: 'CozyNest Weighted Blanket (15 lbs)',
    description: 'Premium glass-bead weighted blanket with removable bamboo duvet cover, 7-layer construction for even weight distribution.',
    price: 89.99, comparePrice: 119.99, discountPercentage: 25,
    sku: 'HME-BLN-017', stock: 65, category: 'Home & Garden',
    tags: ['blanket', 'weighted', 'sleep', 'home'],
    images: [UNSPLASH('1522771739844-6a9f6d5f14af')],
    thumbnail: UNSPLASH('1522771739844-6a9f6d5f14af', 400),
    rating: 4.6, reviewCount: 53,
    attributes: { colors: ['Charcoal Gray', 'Navy', 'Slate Blue'], sizes: ['Twin', 'Queen', 'King'], brand: 'CozyNest' },
    isFeatured: false,
  },
  {
    title: 'PixelPad Pro 12.9" Tablet',
    description: '12.9-inch AMOLED tablet with S-Pen support, 256GB storage, quad speakers, and desktop-class performance.',
    price: 599.99, comparePrice: 749.99, discountPercentage: 20,
    sku: 'TAB-PRO-018', stock: 28, category: 'Electronics',
    tags: ['tablet', 'amoled', 'stylus', 'professional'],
    images: [UNSPLASH('1544244015-0df4b3ffc6b0')],
    thumbnail: UNSPLASH('1544244015-0df4b3ffc6b0', 400),
    rating: 4.7, reviewCount: 44,
    attributes: { colors: ['Graphite', 'Silver'], storage: ['128GB', '256GB'], brand: 'PixelPad' },
    isFeatured: true,
  },
  {
    title: 'VelocityPro Electric Skateboard',
    description: 'High-performance electric skateboard with dual 600W motors, 25 mph top speed, 20-mile range, and regenerative braking.',
    price: 599.99, comparePrice: 799.99, discountPercentage: 25,
    sku: 'SKT-ELC-019', stock: 10, category: 'Outdoor',
    tags: ['skateboard', 'electric', 'outdoor', 'commute'],
    images: [UNSPLASH('1563453392212-326f5e854473')],
    thumbnail: UNSPLASH('1563453392212-326f5e854473', 400),
    rating: 4.5, reviewCount: 19,
    attributes: { colors: ['Matte Black', 'Racing Red'], brand: 'VelocityPro' },
    isFeatured: false,
  },
  {
    title: 'NomadTravel Backpack 40L',
    description: 'Carry-on travel backpack with clamshell opening, hidden laptop compartment, USB-C charging port, and anti-theft zippers.',
    price: 119.99, comparePrice: 159.99, discountPercentage: 25,
    sku: 'TRV-BAG-020', stock: 50, category: 'Travel',
    tags: ['backpack', 'travel', 'carry-on', 'laptop'],
    images: [UNSPLASH('1553062407-987b6e9e199e')],
    thumbnail: UNSPLASH('1553062407-987b6e9e199e', 400),
    rating: 4.8, reviewCount: 67,
    attributes: { colors: ['Obsidian', 'Navy', 'Olive Green'], brand: 'NomadTravel' },
    isFeatured: false,
  },
];

const doctorDefs = [
  {
    name: 'Dr. Sarah Chen',
    specialty: 'Dermatology',
    subSpecialty: 'Cosmetic Dermatology',
    email: 'sarah.chen@clinic.com',
    phone: '+1 555-0201',
    avatar: 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400',
    bio: 'Board-certified dermatologist with 12 years of experience in cosmetic and medical dermatology.',
    qualifications: ['MD - Stanford University', 'Board Certified - AAD'],
    experience: 12,
    rating: 4.9,
    reviewCount: 128,
    consultationFee: 150.00,
    depositRequired: 50.00,
    slotDuration: 30,
  },
  {
    name: 'Dr. Michael Rodriguez',
    specialty: 'General Practice',
    subSpecialty: 'Preventive Medicine',
    email: 'michael.rodriguez@clinic.com',
    phone: '+1 555-0202',
    avatar: 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400',
    bio: 'Family physician focused on preventive care and chronic disease management.',
    qualifications: ['MD - Johns Hopkins', 'Board Certified - ABFM'],
    experience: 18,
    rating: 4.8,
    reviewCount: 215,
    consultationFee: 100.00,
    depositRequired: 0.00,
    slotDuration: 30,
  },
  {
    name: 'Dr. Emily Watson',
    specialty: 'Dental Surgery',
    subSpecialty: 'Orthodontics',
    email: 'emily.watson@clinic.com',
    phone: '+1 555-0203',
    avatar: 'https://images.unsplash.com/photo-1594824476967-48c8b964ac31?w=400',
    bio: 'Experienced orthodontist specializing in Invisalign and cosmetic dental procedures.',
    qualifications: ['DDS - University of Michigan', 'MS Orthodontics'],
    experience: 8,
    rating: 4.7,
    reviewCount: 89,
    consultationFee: 120.00,
    depositRequired: 30.00,
    slotDuration: 45,
  },
  {
    name: 'Dr. James Park',
    specialty: 'Internal Medicine',
    subSpecialty: 'Cardiology',
    email: 'james.park@clinic.com',
    phone: '+1 555-0204',
    avatar: 'https://images.unsplash.com/photo-1382957020522-51fd39641ecf?w=400',
    bio: 'Cardiologist with expertise in preventive cardiology and heart failure management.',
    qualifications: ['MD - Columbia University', 'Board Certified - Cardiology'],
    experience: 15,
    rating: 4.9,
    reviewCount: 156,
    consultationFee: 200.00,
    depositRequired: 75.00,
    slotDuration: 45,
  },
];

const serviceDefs = [
  { name: 'General Consultation', slug: 'general-consultation', description: 'Standard doctor consultation for diagnosis and treatment.', category: 'general', duration: 30, price: 100.00, depositRequired: 0 },
  { name: 'Dermatology Consultation', slug: 'dermatology-consultation', description: 'Specialized skin consultation with examination.', category: 'dermatology', duration: 30, price: 150.00, depositRequired: 50 },
  { name: 'Dental Cleaning', slug: 'dental-cleaning', description: 'Professional teeth cleaning and oral health check.', category: 'dental', duration: 45, price: 120.00, depositRequired: 30 },
  { name: 'Cardiac Screening', slug: 'cardiac-screening', description: 'Comprehensive heart health screening with ECG.', category: 'cardiology', duration: 45, price: 200.00, depositRequired: 75 },
  { name: 'Invisalign Assessment', slug: 'invisalign-assessment', description: 'Initial orthodontic assessment for clear aligner treatment.', category: 'orthodontics', duration: 45, price: 150.00, depositRequired: 50 },
  { name: 'Follow-up Visit', slug: 'follow-up-visit', description: 'Follow-up consultation for existing patients.', category: 'general', duration: 15, price: 60.00, depositRequired: 0 },
  { name: 'Acne Treatment Plan', slug: 'acne-treatment-plan', description: 'Comprehensive acne evaluation and personalized treatment plan.', category: 'dermatology', duration: 30, price: 175.00, depositRequired: 50 },
  { name: 'Annual Physical Exam', slug: 'annual-physical-exam', description: 'Complete annual health checkup with blood work order.', category: 'general', duration: 60, price: 250.00, depositRequired: 0 },
];

const seedData = async () => {
  try {
    console.log('Connecting to PostgreSQL via Sequelize...');
    await sequelize.authenticate();
    console.log('Database connection established.');

    console.log('Syncing database schema (force=true to rebuild)...');
    await sequelize.sync({ force: true });
    console.log('Schema synced.');

    // ── Users ─────────────────────────────────────────────────────────────
    console.log('Seeding Users...');
    const hashedPassword = await bcrypt.hash('Password123!', 10);
    const addr = { street: '100 Silicon Way', city: 'San Francisco', state: 'CA', country: 'USA', zipCode: '94105' };

    const [admin, vendor, customer, customer2] = await Promise.all([
      User.create({ name: 'Admin User', email: 'admin@example.com', password: hashedPassword, role: 'admin', avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150', phone: '+1 555-0100', address: addr, isVerified: true, isActive: true }),
      User.create({ name: 'Vendor Store', email: 'vendor@example.com', password: hashedPassword, role: 'vendor', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150', phone: '+1 555-0101', address: { ...addr, street: '200 Market St', city: 'Austin', state: 'TX' }, isVerified: true, isActive: true }),
      User.create({ name: 'Alex Johnson', email: 'user@example.com', password: hashedPassword, role: 'user', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150', phone: '+1 555-0102', address: { ...addr, street: '350 5th Ave', city: 'New York', state: 'NY' }, isVerified: true, isActive: true }),
      User.create({ name: 'Maria Garcia', email: 'maria@example.com', password: hashedPassword, role: 'user', avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150', phone: '+1 555-0103', address: { ...addr, street: '123 Main St', city: 'Los Angeles', state: 'CA' }, isVerified: true, isActive: true }),
    ]);
    console.log(`Seeded 4 users. (IDs: ${admin.id}, ${vendor.id}, ${customer.id}, ${customer2.id})`);

    // ── Products (20) ────────────────────────────────────────────────────
    console.log('Seeding 20 Products...');
    const products = await Product.bulkCreate(
      productDefs.map(p => ({ ...p, vendor_id: vendor.id })),
      { returning: true }
    );
    console.log(`Seeded ${products.length} products.`);

    // ── Reviews (one per product) ─────────────────────────────────────────
    console.log('Seeding Reviews...');
    const reviewComments = [
      'Incredible sound quality, best ANC I have ever used!',
      'Battery lasts over a week, screen is gorgeous.',
      'The mechanical feel is top-notch, love the RGB.',
      'Solid build, motor is whisper quiet and powerful.',
      'Crystal clear 4K footage, drone is easy to fly.',
      'Fills the whole room with rich bass. Waterproof tested.',
      'Portrait shots are razor sharp, bokeh is creamy.',
      'Perfect thickness, alignment lines are helpful.',
      'Carbon plate makes a noticeable difference at pace.',
      'Three brightness modes, USB-C charging is convenient.',
      'Accurate readings, syncs well with Apple Health.',
      'Fastest laptop I have ever owned, battery is insane.',
      'ANC rivals over-ear headphones, very comfortable.',
      'Herbs grew within a week, app is very intuitive.',
      'Whisper mode is truly silent, PM2.5 display is accurate.',
      'Quick adjust mechanism is smooth, great grip.',
      'Weight distribution is even, bamboo cover is soft.',
      'Stylus support is excellent for note-taking.',
      'Dual motors give serious torque, range is accurate.',
      'Clamshell opening is genius, fits perfectly overhead.',
    ];
    for (let i = 0; i < products.length; i++) {
      await Review.create({
        product_id: products[i].id,
        user_id: customer.id,
        userName: customer.name,
        userAvatar: customer.avatar,
        rating: 4 + (Math.random() > 0.3 ? 1 : 0),
        title: `Great ${products[i].category.toLowerCase()} product`,
        comment: reviewComments[i],
        verifiedPurchase: true,
      });
    }
    console.log(`Seeded ${products.length} reviews.`);

    // ── Orders (15 past orders for dashboard graphs) ──────────────────────
    console.log('Seeding 15 Orders...');
    const statuses = ['delivered', 'delivered', 'delivered', 'shipped', 'processing', 'delivered', 'cancelled', 'delivered', 'processing', 'delivered', 'shipped', 'delivered', 'processing', 'delivered', 'delivered'];
    const carriers = ['FedEx Express', 'UPS Ground', 'USPS Priority', 'DHL Express', 'FedEx Ground', 'UPS Next Day', null, 'FedEx Express', 'UPS Ground', 'USPS Priority', 'DHL Express', 'FedEx Express', 'UPS Ground', 'FedEx Express', 'USPS Priority'];
    const customers = [customer, customer2];
    const orderItems = [];

    for (let i = 0; i < 15; i++) {
      const prod = products[i % products.length];
      const cust = customers[i % 2];
      const qty = 1 + Math.floor(Math.random() * 3);
      const itemsPrice = parseFloat(prod.price) * qty;
      const taxPrice = Math.round(itemsPrice * 0.08 * 100) / 100;
      const shippingPrice = itemsPrice > 100 ? 0 : 9.99;
      const totalPrice = Math.round((itemsPrice + taxPrice + shippingPrice) * 100) / 100;
      const daysAgo = 30 - i * 2;

      await Order.create({
        user_id: cust.id,
        orderNumber: `ORD-202608${String(i + 1).padStart(2, '0')}-${String.fromCharCode(65 + i)}${String.fromCharCode(65 + ((i * 3) % 26))}C`,
        items: [{ product_id: prod.id, title: prod.title, price: parseFloat(prod.price), quantity: qty, image: prod.thumbnail, selectedColor: prod.attributes?.colors?.[0] || '' }],
        shippingAddress: cust.address,
        billingAddress: cust.address,
        paymentMethod: 'stripe',
        itemsPrice, taxPrice, shippingPrice, totalPrice,
        isPaid: statuses[i] !== 'cancelled',
        paidAt: statuses[i] !== 'cancelled' ? new Date(Date.now() - daysAgo * 86400000) : null,
        isDelivered: statuses[i] === 'delivered',
        deliveredAt: statuses[i] === 'delivered' ? new Date(Date.now() - (daysAgo - 3) * 86400000) : null,
        status: statuses[i],
        trackingNumber: carriers[i] ? `TRK-${1000000000 + i}` : '',
        carrier: carriers[i] || '',
      });
    }
    console.log('Seeded 15 orders.');

    // ── Notifications ─────────────────────────────────────────────────────
    console.log('Seeding Notifications...');
    await Notification.bulkCreate([
      { recipient: customer.id, type: 'order', title: 'Order Delivered', message: 'Your order #ORD-20260801-ABC has been delivered.', read: false },
      { recipient: customer.id, type: 'info', title: 'Welcome to LumiCorePro!', message: 'Use code WELCOME15 for 15% off.', read: true, readAt: new Date() },
      { recipient: admin.id, type: 'system', title: 'Database Seeded', message: 'Production-grade seed data loaded successfully.', read: false },
    ]);
    console.log('Seeded 3 notifications.');

    // ── Doctors (4) ──────────────────────────────────────────────────────
    console.log('Seeding Doctors...');
    const doctors = await Doctor.bulkCreate(doctorDefs, { returning: true });
    console.log(`Seeded ${doctors.length} doctors.`);

    // ── Services (8) ─────────────────────────────────────────────────────
    console.log('Seeding Services...');
    const services = await Service.bulkCreate(serviceDefs, { returning: true });
    console.log(`Seeded ${services.length} services.`);

    // ── Bookings (8) ─────────────────────────────────────────────────────
    console.log('Seeding Bookings...');
    const bookingDates = [];
    for (let i = 0; i < 8; i++) {
      const d = new Date();
      d.setDate(d.getDate() + 1 + i);
      bookingDates.push(d.toISOString().slice(0, 10));
    }
    const bookingTimes = ['09:00', '10:00', '11:30', '14:00', '09:30', '10:30', '13:00', '15:00'];
    const bookingStatuses = ['confirmed', 'confirmed', 'pending', 'completed', 'confirmed', 'cancelled', 'confirmed', 'pending'];
    const bookingUsers = [customer, customer2];

    for (let i = 0; i < 8; i++) {
      const doc = doctors[i % doctors.length];
      const svc = services[i % services.length];
      const u = bookingUsers[i % 2];
      await Booking.create({
        user_id: u.id,
        doctor_id: doc.id,
        service_id: svc.id,
        bookingNumber: `BK-202609${String(i + 1).padStart(2, '0')}-${String.fromCharCode(65 + i)}C`,
        date: bookingDates[i],
        time: bookingTimes[i],
        duration: svc.duration,
        status: bookingStatuses[i],
        reason: i % 2 === 0 ? 'Annual checkup' : 'Follow-up consultation',
        patientInfo: {
          firstName: u.name.split(' ')[0],
          lastName: u.name.split(' ')[1] || '',
          phone: u.phone,
          email: u.email,
        },
        totalAmount: parseFloat(svc.price),
        depositAmount: parseFloat(svc.depositRequired),
        paymentStatus: i < 4 ? 'deposit_paid' : 'pending',
      });
    }
    console.log('Seeded 8 bookings.');

    console.log('\n========================================');
    console.log('PRODUCTION SEED COMPLETED!');
    console.log('========================================');
    console.log('Admin:     admin@example.com    / Password123!');
    console.log('Vendor:    vendor@example.com   / Password123!');
    console.log('Customer1: user@example.com     / Password123!');
    console.log('Customer2: maria@example.com    / Password123!');
    console.log('Products: 20 | Orders: 15 | Doctors: 4 | Services: 8 | Bookings: 8');
    console.log('========================================\n');

    await sequelize.close();
    process.exit(0);
  } catch (error) {
    console.error('\nError during seeding:', error.message || error);
    if (error.original) console.error('DB error:', error.original.message);
    process.exit(1);
  }
};

seedData();
