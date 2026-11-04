import { z } from 'zod';

export const registerSchema = z.object({
  name: z.string().trim().min(2, 'Name must be at least 2 characters').max(80),
  email: z.email('Enter a valid email address').max(160).toLowerCase(),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(128)
    .regex(/[A-Za-z]/, 'Include at least one letter')
    .regex(/[0-9]/, 'Include at least one number'),
});

export const loginSchema = z.object({
  email: z.email('Enter a valid email address').max(160).toLowerCase(),
  password: z.string().min(1, 'Password is required').max(128),
  remember: z.boolean().optional().default(false),
});

export const inquirySchema = z.object({
  vehicleId: z.string().optional().nullable(),
  name: z.string().trim().min(2, 'Name must be at least 2 characters').max(120),
  email: z.email('Enter a valid email address').max(160).toLowerCase(),
  phone: z.string().trim().max(40).optional().or(z.literal('')),
  message: z
    .string()
    .trim()
    .min(10, 'Tell us at least 10 characters')
    .max(4000, 'Message must be under 4000 characters'),
  locale: z.string().max(8).default('en'),
  consentGiven: z.literal(true, { message: 'Consent is required' }),
  idempotencyKey: z.string().min(8).max(120),
});

export const vehicleQuerySchema = z.object({
  q: z.string().trim().max(120).optional(),
  make: z.string().trim().max(60).optional(),
  priceMax: z.coerce.number().positive().optional(),
  sort: z.enum(['newest', 'price-asc', 'price-desc', 'mileage-asc']).default('newest'),
  page: z.coerce.number().int().min(1).max(500).default(1),
  perPage: z.coerce.number().int().min(1).max(48).default(9),
});

export const vehicleCreateSchema = z.object({
  make: z.string().trim().min(1).max(60),
  model: z.string().trim().min(1).max(60),
  year: z.coerce.number().int().min(1900).max(new Date().getFullYear() + 2),
  title: z.string().trim().min(4).max(160),
  description: z.string().trim().min(20).max(6000),
  price: z.coerce.number().positive().max(100_000_000),
  currency: z.string().length(3).default('USD'),
  mileage: z.coerce.number().int().min(0).max(2_000_000),
  mileageUnit: z.enum(['mi', 'km']).default('mi'),
  bodyStyle: z.string().trim().min(1).max(60),
  fuelType: z.string().trim().min(1).max(40),
  transmission: z.string().trim().min(1).max(40),
  locationCountry: z.string().trim().min(2).max(60),
  locationRegion: z.string().trim().min(1).max(80),
  status: z.enum(['draft', 'active', 'reserved', 'sold', 'withdrawn']).default('draft'),
  media: z.array(z.object({ url: z.url(), alt: z.string().max(160).default('') })).default([]),
  provenanceVerified: z.boolean().default(false),
  conditionNotes: z.string().max(2000).optional(),
  conditionReportUrl: z.url().optional().or(z.literal('')),
  vin: z.string().max(32).optional(),
});

export type RegisterInput = z.infer<typeof registerSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type InquiryInput = z.infer<typeof inquirySchema>;
export type VehicleQuery = z.infer<typeof vehicleQuerySchema>;
export type VehicleCreateInput = z.infer<typeof vehicleCreateSchema>;
