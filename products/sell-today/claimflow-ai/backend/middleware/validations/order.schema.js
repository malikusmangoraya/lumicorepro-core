import { z } from 'zod';

const orderItemSchema = z.object({
  product_id: z.number().int().positive(),
  title: z.string().min(1).max(255),
  price: z.number().positive(),
  quantity: z.number().int().min(1).max(999),
  image: z.string().optional().default(''),
  selectedColor: z.string().optional(),
  selectedSize: z.string().optional(),
});

const addressSchema = z.object({
  street: z.string().min(1, 'Street is required').max(255),
  city: z.string().min(1, 'City is required').max(100),
  state: z.string().min(1, 'State is required').max(100),
  country: z.string().min(1, 'Country is required').max(100),
  zipCode: z.string().min(1, 'Zip code is required').max(20),
});

export const createOrderSchema = z.object({
  body: z.object({
    items: z.array(orderItemSchema).min(1, 'Order must contain at least one item').max(50),
    shippingAddress: addressSchema,
    billingAddress: addressSchema.optional(),
    paymentMethod: z.enum(['stripe', 'paypal', 'credit_card', 'cod'], {
      errorMap: () => ({ message: 'Payment method must be stripe, paypal, credit_card, or cod' }),
    }),
    notes: z.string().max(500).optional().default(''),
    promoCode: z.string().max(50).optional(),
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

export const orderIdParamSchema = z.object({
  params: z.object({
    id: z.string().min(1, 'Order ID is required'),
  }),
});
