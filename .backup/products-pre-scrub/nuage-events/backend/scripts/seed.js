/**
 * LumicorePro — PostgreSQL/Sequelize Database Seeder
 * Usage: node backend/scripts/seed.js
 * Run from project root with backend/.env loaded.
 */
import dotenv from 'dotenv';
import bcrypt from 'bcryptjs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../.env') });

// ── Import Sequelize connection & models ────────────────────────────────────
import { sequelize } from '../config/database.js';
import User from '../models/User.js';
import Product from '../models/Product.js';
import Order from '../models/Order.js';
import Review from '../models/Review.js';
import Notification from '../models/Notification.js';

const seedData = async () => {
  try {
    console.log('🔄 Connecting to PostgreSQL via Sequelize...');
    await sequelize.authenticate();
    console.log('✅ Database connection established.');

    // Sync tables (alter:false to avoid destructive changes in prod)
    console.log('🔧 Syncing database schema...');
    await sequelize.sync({ alter: true });
    console.log('✅ Schema synced.');

    // ── Clear existing data ─────────────────────────────────────────────────
    console.log('🧹 Clearing existing data...');
    await Notification.destroy({ where: {}, truncate: true, cascade: true });
    await Order.destroy({ where: {}, truncate: true, cascade: true });
    await Review.destroy({ where: {}, truncate: true, cascade: true });
    await Product.destroy({ where: {}, truncate: true, cascade: true });
    await User.destroy({ where: {}, truncate: true, cascade: true });
    console.log('✅ Existing data cleared.');

    // ── 1. Seed Users ───────────────────────────────────────────────────────
    console.log('👤 Seeding Users...');
    const hashedPassword = await bcrypt.hash('Password123!', 10);

    const sharedAddress = {
      street: '100 Silicon Way',
      city: 'San Francisco',
      state: 'CA',
      country: 'USA',
      zipCode: '94105',
    };

    const [admin, vendor, customer] = await Promise.all([
      User.create({
        name: 'Admin User',
        email: 'admin@example.com',
        password: hashedPassword,
        role: 'admin',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
        phone: '+1 555-0100',
        address: sharedAddress,
        isVerified: true,
        isActive: true,
        preferences: { theme: 'dark', language: 'en' },
      }),
      User.create({
        name: 'Vendor Store',
        email: 'vendor@example.com',
        password: hashedPassword,
        role: 'vendor',
        avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
        phone: '+1 555-0101',
        address: {
          ...sharedAddress,
          street: '200 Market Street',
          city: 'Austin',
          state: 'TX',
          zipCode: '78701',
        },
        isVerified: true,
        isActive: true,
        preferences: { theme: 'dark', language: 'en' },
      }),
      User.create({
        name: 'Alex Johnson',
        email: 'user@example.com',
        password: hashedPassword,
        role: 'user',
        avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
        phone: '+1 555-0102',
        address: {
          ...sharedAddress,
          street: '350 5th Avenue',
          city: 'New York',
          state: 'NY',
          zipCode: '10118',
        },
        isVerified: true,
        isActive: true,
        preferences: { theme: 'light', language: 'en' },
      }),
    ]);

    console.log(`✅ Seeded 3 users. (IDs: ${admin.id}, ${vendor.id}, ${customer.id})`);

    // ── 2. Seed Products ────────────────────────────────────────────────────
    console.log('📦 Seeding Products...');

    const productDefs = [
      {
        title: 'LumiCore SoundPro Wireless ANC Headphones',
        description:
          'Premium active noise-cancelling over-ear headphones with 40-hour battery life, high-res audio certification, and ultra-plush memory foam earcups.',
        price: 249.99,
        comparePrice: 299.99,
        discountPercentage: 17,
        sku: 'LUMI-AUD-001',
        stock: 45,
        category: 'Audio',
        tags: ['headphones', 'anc', 'wireless', 'bluetooth'],
        images: [
          'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800',
          'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800',
        ],
        thumbnail: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
        rating: 4.8,
        reviewCount: 38,
        attributes: {
          colors: ['Midnight Black', 'Platinum Silver', 'Navy Blue'],
          brand: 'LumiCore Audio',
        },
        vendor_id: vendor.id,
        isFeatured: true,
      },
      {
        title: 'UltraSync Smart Watch Series X',
        description:
          'Next-generation smartwatch featuring AMOLED display, ECG monitoring, SpO2 sensor, built-in GPS, and 7-day battery life.',
        price: 199.99,
        comparePrice: 249.99,
        discountPercentage: 20,
        sku: 'LUMI-WCH-002',
        stock: 60,
        category: 'Wearables',
        tags: ['smartwatch', 'fitness', 'gps', 'health'],
        images: ['https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800'],
        thumbnail: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400',
        rating: 4.9,
        reviewCount: 52,
        attributes: {
          colors: ['Space Gray', 'Rose Gold', 'Silver'],
          sizes: ['40mm', '44mm'],
          brand: 'UltraSync',
        },
        vendor_id: vendor.id,
        isFeatured: true,
      },
      {
        title: 'ProMech RGB Mechanical Keyboard',
        description:
          'Customizable hot-swappable mechanical keyboard with per-key RGB lighting, PBT double-shot keycaps, and durable aluminum chassis.',
        price: 129.99,
        comparePrice: 159.99,
        discountPercentage: 19,
        sku: 'LUMI-KEY-003',
        stock: 30,
        category: 'Accessories',
        tags: ['keyboard', 'gaming', 'rgb', 'mechanical'],
        images: ['https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800'],
        thumbnail: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400',
        rating: 4.7,
        reviewCount: 24,
        attributes: { colors: ['Chalk White', 'Matte Black'], brand: 'ProMech' },
        vendor_id: vendor.id,
        isFeatured: true,
      },
      {
        title: 'ErgoLift Dual-Motor Standing Desk',
        description:
          'Heavy-duty electric height-adjustable desk with memory presets, solid oak tabletop, integrated cable management, and anti-collision sensor.',
        price: 499.99,
        comparePrice: 599.99,
        discountPercentage: 16,
        sku: 'LUMI-DSK-004',
        stock: 15,
        category: 'Home Office',
        tags: ['desk', 'standing desk', 'ergonomic', 'furniture'],
        images: ['https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800'],
        thumbnail: 'https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=400',
        rating: 4.9,
        reviewCount: 19,
        attributes: {
          colors: ['Walnut', 'Natural Oak'],
          sizes: ['48x30', '60x30'],
          brand: 'ErgoLift',
        },
        vendor_id: vendor.id,
        isFeatured: true,
      },
      {
        title: 'AeroAir 4K Ultra HD Drone',
        description:
          'Compact foldable camera drone with 3-axis gimbal, 4K 60fps HDR video, obstacle avoidance, and 34-minute flight time.',
        price: 349.99,
        comparePrice: 429.99,
        discountPercentage: 18,
        sku: 'LUMI-DRN-005',
        stock: 22,
        category: 'Electronics',
        tags: ['drone', 'camera', '4k', 'photography'],
        images: ['https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=800'],
        thumbnail: 'https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=400',
        rating: 4.6,
        reviewCount: 14,
        attributes: { colors: ['Arctic White', 'Carbon Gray'], brand: 'AeroAir' },
        vendor_id: vendor.id,
        isFeatured: false,
      },
      {
        title: 'PureSound Hi-Fi Bluetooth Speaker',
        description:
          '360-degree immersive sound with deep bass reflex, IPX7 waterproof rating, and 24 hours of party playtime.',
        price: 79.99,
        comparePrice: 99.99,
        discountPercentage: 20,
        sku: 'LUMI-SPK-006',
        stock: 80,
        category: 'Audio',
        tags: ['speaker', 'bluetooth', 'waterproof', 'portable'],
        images: ['https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800'],
        thumbnail: 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400',
        rating: 4.5,
        reviewCount: 42,
        attributes: { colors: ['Forest Green', 'Charcoal', 'Coral Red'], brand: 'PureSound' },
        vendor_id: vendor.id,
        isFeatured: false,
      },
    ];

    const products = await Product.bulkCreate(productDefs, { returning: true });
    console.log(`✅ Seeded ${products.length} products.`);

    // ── 3. Seed Reviews ─────────────────────────────────────────────────────
    console.log('⭐ Seeding Reviews...');

    await Review.bulkCreate([
      {
        product_id: products[0].id,
        user_id: customer.id,
        userName: customer.name,
        userAvatar: customer.avatar,
        rating: 5,
        title: 'Outstanding sound quality and battery life',
        comment:
          'Hands down the most comfortable ANC headphones I have ever used. The noise cancelling is whisper quiet and the soundstage is deep.',
        verifiedPurchase: true,
      },
      {
        product_id: products[1].id,
        user_id: customer.id,
        userName: customer.name,
        userAvatar: customer.avatar,
        rating: 5,
        title: 'Sleek and very accurate sensors',
        comment:
          'The battery easily lasts 6-7 days. Notifications are crisp and heart rate tracking is pinpoint accurate.',
        verifiedPurchase: true,
      },
      {
        product_id: products[2].id,
        user_id: customer.id,
        userName: customer.name,
        userAvatar: customer.avatar,
        rating: 4,
        title: 'Great keyboard, satisfying feel',
        comment:
          'The tactile feedback is excellent. The RGB lighting is very vivid. Would love a numpad version.',
        verifiedPurchase: true,
      },
    ]);

    console.log('✅ Seeded 3 reviews.');

    // ── 4. Seed Orders ──────────────────────────────────────────────────────
    console.log('🛍️ Seeding Orders...');

    const customerAddr = {
      street: '350 5th Avenue',
      city: 'New York',
      state: 'NY',
      country: 'USA',
      zipCode: '10118',
    };

    await Order.bulkCreate([
      {
        user_id: customer.id,
        orderNumber: 'ORD-20260901-A1B2C',
        items: [
          {
            product_id: products[0].id,
            title: products[0].title,
            price: 249.99,
            quantity: 1,
            image: products[0].thumbnail,
            selectedColor: 'Midnight Black',
          },
          {
            product_id: products[2].id,
            title: products[2].title,
            price: 129.99,
            quantity: 1,
            image: products[2].thumbnail,
            selectedColor: 'Chalk White',
          },
        ],
        shippingAddress: customerAddr,
        billingAddress: customerAddr,
        paymentMethod: 'stripe',
        itemsPrice: 379.98,
        taxPrice: 30.4,
        shippingPrice: 0.0,
        totalPrice: 410.38,
        isPaid: true,
        paidAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        isDelivered: true,
        deliveredAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
        status: 'delivered',
        trackingNumber: 'TRK-9823749281',
        carrier: 'FedEx Express',
      },
      {
        user_id: customer.id,
        orderNumber: 'ORD-20260902-D4E5F',
        items: [
          {
            product_id: products[1].id,
            title: products[1].title,
            price: 199.99,
            quantity: 1,
            image: products[1].thumbnail,
            selectedColor: 'Space Gray',
          },
        ],
        shippingAddress: customerAddr,
        billingAddress: customerAddr,
        paymentMethod: 'stripe',
        itemsPrice: 199.99,
        taxPrice: 16.0,
        shippingPrice: 0.0,
        totalPrice: 215.99,
        isPaid: true,
        paidAt: new Date(),
        status: 'processing',
        trackingNumber: 'TRK-1092837465',
        carrier: 'UPS Ground',
      },
    ]);

    console.log('✅ Seeded 2 sample orders.');

    // ── 5. Seed Notifications ────────────────────────────────────────────────
    console.log('🔔 Seeding Notifications...');

    await Notification.bulkCreate([
      {
        recipient: customer.id,
        type: 'order',
        title: 'Order Delivered',
        message: 'Your order #ORD-20260901-A1B2C has been safely delivered to your doorstep.',
        link: '/templates/ecommerce/OrdersHistory',
        read: false,
        metadata: {},
      },
      {
        recipient: customer.id,
        type: 'info',
        title: 'Welcome to LumiCorePro!',
        message:
          'Thank you for joining LumiCorePro. Explore our catalog with 15% off using code WELCOME15.',
        link: '/templates/ecommerce/ProductListing',
        read: true,
        readAt: new Date(),
        metadata: {},
      },
      {
        recipient: admin.id,
        type: 'system',
        title: 'Database Seeded',
        message: 'The database has been seeded with demo data successfully.',
        link: '/templates/dashboard/DashboardOverview',
        read: false,
        metadata: {},
      },
    ]);

    console.log('✅ Seeded 3 notifications.');

    console.log('\n========================================');
    console.log('🎉 SEEDING COMPLETED SUCCESSFULLY!');
    console.log('========================================');
    console.log('Admin Account:    admin@example.com     / Password123!');
    console.log('Vendor Account:   vendor@example.com    / Password123!');
    console.log('Customer Account: user@example.com      / Password123!');
    console.log('========================================\n');

    await sequelize.close();
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Error during database seeding:');
    console.error(error.message || error);
    if (error.original) console.error('DB error:', error.original.message);
    process.exit(1);
  }
};

seedData();
