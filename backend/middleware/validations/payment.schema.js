import { z } from 'zod';

export const createPaymentIntentSchema = z.object({
  body: z.object({
    orderId: z.number().int().positive().optional(),
    amount: z.number().positive('Amount must be positive').max(999999.99).optional(),
    currency: z.string().length(3, 'Currency must be 3 characters').optional().default('usd'),
  }),
});

export const confirmPaymentSchema = z.object({
  body: z.object({
    paymentIntentId: z.string().min(1, 'Payment intent ID is required'),
    orderId: z.number().int().positive().optional(),
    cardDetails: z.object({
      charge: z.string().optional(),
      last4: z.string().length(4).optional(),
      brand: z.string().optional(),
    }).optional(),
  }),
});

export const refundSchema = z.object({
  body: z.object({
    paymentId: z.number().int().positive('Payment ID is required'),
    amount: z.number().positive().max(999999.99).optional(),
    reason: z.string().max(500).optional(),
  }),
});

export const checkoutSchema = z.object({
  body: z.object({
    planId: z.number().int().positive().optional(),
    orderId: z.number().int().positive().optional(),
    successUrl: z.string().url('Success URL must be valid').optional(),
    cancelUrl: z.string().url('Cancel URL must be valid').optional(),
    agentApiKey: z.string().max(200).optional(),
  }),
});
