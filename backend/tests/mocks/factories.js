/**
 * Shared Mock Factories
 * ---------------------
 * Deterministic builders for common entities used across the test suite
 * (users, products, payments). Never hit real APIs or DB in tests.
 */

export const makeUser = (overrides = {}) => ({
  id: 1,
  name: 'Test User',
  email: 'test@example.com',
  role: 'user',
  password: '$2b$10$hashedpassword',
  avatar: '',
  isActive: true,
  twoFactorEnabled: false,
  preferences: { theme: 'dark' },
  createdAt: new Date('2026-01-01'),
  updatedAt: new Date('2026-01-01'),
  comparePassword: jest.fn(async () => true),
  toJSON() { return { ...this }; },
  ...overrides,
});

export const makeAdmin = (overrides = {}) =>
  makeUser({ id: 2, name: 'Admin', email: 'admin@example.com', role: 'admin', ...overrides });

export const makeProduct = (overrides = {}) => ({
  id: 10,
  title: 'Wireless Headphones',
  slug: 'wireless-headphones',
  description: 'Noise cancelling over-ear headphones',
  price: 99.99,
  comparePrice: 149.99,
  category: 'Audio',
  stock: 25,
  rating: 4.5,
  reviewCount: 120,
  isActive: true,
  isFeatured: true,
  thumbnail: 'https://example.com/img.jpg',
  images: ['https://example.com/img.jpg'],
  vendor_id: 1,
  createdAt: new Date('2026-01-01'),
  updatedAt: new Date('2026-01-01'),
  toJSON() { return { ...this }; },
  ...overrides,
});

export const makeOrder = (overrides = {}) => ({
  id: 100,
  user_id: 1,
  orderNumber: 'ORD-20260101-ABC12',
  shippingAddress: { line1: '123 Main St', city: 'Karachi', country: 'PK' },
  billingAddress: { line1: '123 Main St', city: 'Karachi', country: 'PK' },
  paymentMethod: 'stripe',
  itemsPrice: 99.99,
  taxPrice: 8.0,
  shippingPrice: 0,
  totalPrice: 107.99,
  isPaid: true,
  status: 'processing',
  items: [
    { product_id: 10, title: 'Wireless Headphones', price: 99.99, quantity: 1, image: '' },
  ],
  createdAt: new Date('2026-01-01'),
  updatedAt: new Date('2026-01-01'),
  toJSON() { return { ...this }; },
  ...overrides,
});

export const makePayment = (overrides = {}) => ({
  id: 500,
  user_id: 1,
  order_id: 100,
  stripePaymentIntentId: 'pi_mock_123456',
  amount: 107.99,
  currency: 'usd',
  status: 'succeeded',
  provider: 'stripe',
  paymentMethod: 'card',
  createdAt: new Date('2026-01-01'),
  updatedAt: new Date('2026-01-01'),
  toJSON() { return { ...this }; },
  ...overrides,
});