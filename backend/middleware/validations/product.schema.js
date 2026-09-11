import { z } from 'zod';

export const createProductSchema = z.object({
  body: z.object({
    title: z.string().trim().min(1, 'Product title is required').max(255),
    description: z.string().min(10, 'Description must be at least 10 characters').max(5000),
    price: z.number().positive('Price must be positive').max(999999.99),
    comparePrice: z.number().positive().max(999999.99).optional().default(0),
    discountPercentage: z.number().min(0).max(100).optional().default(0),
    sku: z.string().max(100).optional(),
    stock: z.number().int().min(0, 'Stock cannot be negative'),
    category: z.string().trim().min(1, 'Category is required').max(100),
    tags: z.array(z.string().max(50)).max(20).optional().default([]),
    images: z.array(z.string().url('Each image must be a valid URL')).max(10).optional().default([]),
    thumbnail: z.string().url('Thumbnail must be a valid URL').optional().default(''),
    attributes: z.record(z.any()).optional().default({}),
    isFeatured: z.boolean().optional().default(false),
    isActive: z.boolean().optional().default(true),
  }),
});

export const updateProductSchema = z.object({
  body: z.object({
    title: z.string().trim().min(1).max(255).optional(),
    description: z.string().min(10).max(5000).optional(),
    price: z.number().positive().max(999999.99).optional(),
    comparePrice: z.number().positive().max(999999.99).optional(),
    discountPercentage: z.number().min(0).max(100).optional(),
    sku: z.string().max(100).optional().nullable(),
    stock: z.number().int().min(0).optional(),
    category: z.string().trim().min(1).max(100).optional(),
    tags: z.array(z.string().max(50)).max(20).optional(),
    images: z.array(z.string().url()).max(10).optional(),
    thumbnail: z.string().optional(),
    attributes: z.record(z.any()).optional(),
    isFeatured: z.boolean().optional(),
    isActive: z.boolean().optional(),
  }),
  params: z.object({
    id: z.string().regex(/^\d+$/, 'Product ID must be a number'),
  }),
});

export const productQuerySchema = z.object({
  query: z.object({
    page: z.string().regex(/^\d+$/).optional(),
    limit: z.string().regex(/^\d+$/).optional(),
    category: z.string().max(100).optional(),
    minPrice: z.string().regex(/^\d+(\.\d+)?$/).optional(),
    maxPrice: z.string().regex(/^\d+(\.\d+)?$/).optional(),
    rating: z.string().regex(/^\d+(\.\d+)?$/).optional(),
    inStock: z.enum(['true', 'false']).optional(),
    search: z.string().max(200).optional(),
    sort: z.enum(['price-asc', 'price-desc', 'rating', 'popular', 'oldest', 'newest']).optional(),
    isFeatured: z.enum(['true', 'false']).optional(),
  }),
});

export const addReviewSchema = z.object({
  body: z.object({
    rating: z.number().int().min(1, 'Rating must be between 1 and 5').max(5),
    title: z.string().trim().max(200).optional().default(''),
    comment: z.string().trim().min(1, 'Comment is required').max(2000),
  }),
  params: z.object({
    id: z.string().regex(/^\d+$/, 'Product ID must be a number'),
  }),
});
