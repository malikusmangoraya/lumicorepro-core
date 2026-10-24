import { z } from 'zod';

/**
 * The checkout payload is what `services/orderService.js#createOrder` reads, no
 * more: a line item is a product id and a quantity. Title, price and image come
 * from the catalog under a `FOR UPDATE` row lock, so a client that sends them
 * gets them stripped here rather than ignored deeper down.
 */
const orderItemSchema = z.object({
  product: z.number().int().positive('Product ID must be a positive integer'),
  quantity: z.number().int().min(1, 'Quantity must be at least 1').max(999),
  selectedColor: z.string().max(50).optional(),
  selectedSize: z.string().max(50).optional(),
});

const addressSchema = z.object({
  fullName: z.string().min(1).max(120).optional(),
  phone: z.string().max(30).optional(),
  street: z.string().min(1, 'Street is required').max(255),
  city: z.string().min(1, 'City is required').max(100),
  state: z.string().min(1, 'State is required').max(100),
  country: z.string().min(1, 'Country is required').max(100),
  zipCode: z.string().min(1, 'Zip code is required').max(20),
});

export const createOrderSchema = z.object({
  body: z.object({
    items: z.array(orderItemSchema).min(1, 'Order must contain at least one item').max(50, 'An order holds at most 50 lines'),
    shippingAddress: addressSchema,
    billingAddress: addressSchema.optional(),
    paymentMethod: z.enum(['stripe', 'paypal', 'credit_card', 'cod'], {
      errorMap: () => ({ message: 'Payment method must be stripe, paypal, credit_card, or cod' }),
    }),
    notes: z.string().max(500).optional().default(''),
    promoCode: z.string().trim().max(50).optional(),
    currency: z
      .string()
      .trim()
      .regex(/^[A-Za-z]{3}$/, 'Currency must be a 3-letter code')
      .optional(),
  }),
});

export const updateOrderStatusSchema = z.object({
  body: z.object({
    status: z.enum(['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']),
    trackingNumber: z.string().max(100).optional(),
    carrier: z.string().max(100).optional(),
  }),
  params: z.object({
    id: z.string().regex(/^\d+$/, 'Order ID must be a number'),
  }),
});
