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
  bodyStyle: z.string().trim().max(60).optional(),
  fuelType: z.string().trim().max(40).optional(),
  transmission: z.string().trim().max(40).optional(),
  priceMin: z.coerce.number().nonnegative().optional(),
  priceMax: z.coerce.number().positive().optional(),
  yearMin: z.coerce.number().int().min(1900).max(2100).optional(),
  mileageMax: z.coerce.number().int().nonnegative().optional(),
  sort: z.enum(['newest', 'price-asc', 'price-desc', 'mileage-asc', 'year-desc']).default('newest'),
  page: z.coerce.number().int().min(1).max(500).default(1),
  perPage: z.coerce.number().int().min(1).max(48).default(9),
  /** Comma-separated slugs, used by the saved and compare trays. */
  slugs: z.string().trim().max(600).optional(),
});

export const orderStatusSchema = z.enum([
  'pending',
  'paid',
  'processing',
  'shipped',
  'delivered',
  'cancelled',
  'refunded',
]);

export const orderQuerySchema = z.object({
  scope: z.enum(['mine', 'all']).default('mine'),
  status: orderStatusSchema.optional(),
  q: z.string().trim().max(120).optional(),
  page: z.coerce.number().int().min(1).max(500).default(1),
  perPage: z.coerce.number().int().min(1).max(100).default(20),
});

export const orderUpdateSchema = z.object({
  status: orderStatusSchema.optional(),
  carrier: z.string().trim().max(60).optional(),
  trackingNumber: z.string().trim().max(80).optional(),
  notes: z.string().trim().max(2000).optional(),
});

/** A phone/manual order: one vehicle or one shop product, not a cart. */
export const orderCreateSchema = z
  .object({
    customerEmail: z.email('Enter a valid email address').max(160).toLowerCase(),
    vehicleSlug: z.string().trim().max(180).optional(),
    productSlug: z.string().trim().max(180).optional(),
    quantity: z.coerce.number().int().min(1).max(99).default(1),
    unitPrice: z.coerce.number().positive().max(100_000_000).optional(),
    shipping: z.coerce.number().nonnegative().max(100_000).default(0),
    discount: z.coerce.number().nonnegative().max(100_000_000).default(0),
    notes: z.string().trim().max(2000).optional(),
  })
  .refine((value) => Boolean(value.vehicleSlug) !== Boolean(value.productSlug), {
    message: 'Provide exactly one of vehicleSlug or productSlug',
    path: ['vehicleSlug'],
  });

export const newsletterSchema = z.object({
  email: z.email('Enter a valid email address').max(160).toLowerCase(),
  source: z.string().trim().max(40).default('footer'),
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
  inspectionReferences: z.array(z.string().trim().max(200)).max(20).default([]),
  provenanceVerified: z.boolean().default(false),
  isFeatured: z.boolean().default(false),
  conditionNotes: z.string().max(2000).optional(),
  conditionReportUrl: z.url().optional().or(z.literal('')),
  vin: z.string().max(32).optional(),
});

export const vehicleStatusSchema = z.enum([
  'draft',
  'active',
  'reserved',
  'sold',
  'withdrawn',
]);

/** Every field optional: a PATCH sends only what changed. */
export const vehicleUpdateSchema = vehicleCreateSchema
  .partial()
  .extend({ status: vehicleStatusSchema.optional() });

export const inquiryStatusSchema = z.enum([
  'new',
  'contacted',
  'viewing_scheduled',
  'closed',
  'spam',
]);

export const inquiryUpdateSchema = z.object({
  status: inquiryStatusSchema.optional(),
  adminNotes: z.string().trim().max(4000).optional(),
});

export const inquiryQuerySchema = z.object({
  scope: z.enum(['mine', 'all']).default('mine'),
  status: inquiryStatusSchema.optional(),
  page: z.coerce.number().int().min(1).max(500).default(1),
  perPage: z.coerce.number().int().min(1).max(100).default(25),
});

export type RegisterInput = z.infer<typeof registerSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type InquiryInput = z.infer<typeof inquirySchema>;
export type VehicleQuery = z.infer<typeof vehicleQuerySchema>;
export type VehicleUpdateInput = z.infer<typeof vehicleUpdateSchema>;
export type VehicleStatus = z.infer<typeof vehicleStatusSchema>;
export type InquiryStatus = z.infer<typeof inquiryStatusSchema>;
export type InquiryUpdateInput = z.infer<typeof inquiryUpdateSchema>;
export type InquiryQuery = z.infer<typeof inquiryQuerySchema>;
export type NewsletterInput = z.infer<typeof newsletterSchema>;
export type OrderStatusValue = z.infer<typeof orderStatusSchema>;
export type OrderQuery = z.infer<typeof orderQuerySchema>;
export type OrderUpdateInput = z.infer<typeof orderUpdateSchema>;
export type OrderCreateInput = z.infer<typeof orderCreateSchema>;
export type VehicleCreateInput = z.infer<typeof vehicleCreateSchema>;
