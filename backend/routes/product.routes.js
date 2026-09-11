import express from 'express';
import { Op } from 'sequelize';
import { body, validationResult } from 'express-validator';
import Product from '../models/Product.js';
import Review from '../models/Review.js';
import User from '../models/User.js';
import { protect, authorize } from '../middleware/auth.js';
import cache from '../services/cache/cache.service.js';
import logger from '../utils/logger.js';

const router = express.Router();

/** Build a stable cache key for GET list requests (filters+page+sort). */
function listKey(query) {
  return Object.entries(query)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${String(v).slice(0, 40)}`)
    .join('&');
}

/**
 * @swagger
 * /api/products:
 *   get:
 *     summary: Get all products with filtering, sorting, pagination
 *     tags: [Products]
 */
router.get('/', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 12;
    const offset = (page - 1) * limit;

    const { category, minPrice, maxPrice, rating, inStock, search, sort, isFeatured } = req.query;

    const where = { isActive: true };

    if (category && category !== 'all') {
      where.category = { [Op.iLike]: category };
    }

    if (minPrice || maxPrice) {
      where.price = {};
      if (minPrice) where.price[Op.gte] = Number(minPrice);
      if (maxPrice) where.price[Op.lte] = Number(maxPrice);
    }

    if (rating) {
      where.rating = { [Op.gte]: Number(rating) };
    }

    if (inStock === 'true') {
      where.stock = { [Op.gt]: 0 };
    }

    if (isFeatured === 'true') {
      where.isFeatured = true;
    }

    if (search) {
      where[Op.or] = [
        { title: { [Op.iLike]: `%${search}%` } },
        { description: { [Op.iLike]: `%${search}%` } },
      ];
    }

    let order = [['createdAt', 'DESC']];
    if (sort === 'price-asc') order = [['price', 'ASC']];
    else if (sort === 'price-desc') order = [['price', 'DESC']];
    else if (sort === 'rating') order = [['rating', 'DESC']];
    else if (sort === 'popular') order = [['reviewCount', 'DESC']];
    else if (sort === 'oldest') order = [['createdAt', 'ASC']];

    const key = listKey(req.query);
    const cached = await cache.get('products', key);
    if (cached) return res.json({ success: true, ...cached, meta: { cached: true, ...(cached.meta || {}) } });

    const { count: total, rows: products } = await Product.findAndCountAll({
      where,
      order,
      limit,
      offset,
      include: [
        {
          model: User,
          as: 'vendor',
          attributes: ['id', 'name', 'email', 'avatar'],
          required: false,
        },
      ],
    });

    const result = {
      count: products.length,
      total,
      pagination: { page, limit, pages: Math.ceil(total / limit) },
      data: products,
    };
    await cache.set('products', key, result, cache.TTL.PRODUCT_LIST);
    return res.json({ success: true, ...result });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products/categories:
 *   get:
 *     summary: Get all distinct product categories with counts
 *     tags: [Products]
 */
router.get('/categories', async (req, res, next) => {
  try {
    const cached = await cache.get('products', 'categories');
    if (cached) return res.json({ success: true, data: cached, meta: { cached: true } });

    const { sequelize } = await import('../config/database.js');
    const categories = await Product.findAll({
      attributes: [
        'category',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      where: { isActive: true },
      group: ['category'],
      order: [[sequelize.literal('count'), 'DESC']],
      raw: true,
    });

    const data = categories.map((c) => ({ name: c.category, count: parseInt(c.count, 10) }));
    await cache.set('products', 'categories', data, cache.TTL.PRODUCT_LIST);
    return res.json({ success: true, data });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products/featured:
 *   get:
 *     summary: Get featured products
 *     tags: [Products]
 */
router.get('/featured', async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 8;
    const products = await Product.findAll({
      where: { isFeatured: true, isActive: true },
      include: [
        {
          model: User,
          as: 'vendor',
          attributes: ['id', 'name', 'avatar'],
          required: false,
        },
      ],
      order: [['rating', 'DESC']],
      limit,
    });

    res.json({
      success: true,
      count: products.length,
      data: products,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products/search:
 *   get:
 *     summary: Search products by keyword
 *     tags: [Products]
 */
router.get('/search', async (req, res, next) => {
  try {
    const { query } = req.query;
    if (!query) {
      return res.status(400).json({ success: false, error: 'Query parameter is required' });
    }

    const products = await Product.findAll({
      where: {
        isActive: true,
        [Op.or]: [
          { title: { [Op.iLike]: `%${query}%` } },
          { description: { [Op.iLike]: `%${query}%` } },
          { category: { [Op.iLike]: `%${query}%` } },
        ],
      },
      limit: 20,
    });

    res.json({
      success: true,
      count: products.length,
      data: products,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products/{id}:
 *   get:
 *     summary: Get single product by ID or slug
 *     tags: [Products]
 */
router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const isNumericId = /^\d+$/.test(id);

    const product = await Product.findOne({
      where: isNumericId ? { id } : { slug: id, isActive: true },
      include: [
        {
          model: User,
          as: 'vendor',
          attributes: ['id', 'name', 'email', 'avatar'],
          required: false,
        },
      ],
    });

    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    const reviews = await Review.findAll({
      where: { product_id: product.id },
      include: [
        {
          model: User,
          as: 'user',
          attributes: ['id', 'name', 'avatar'],
          required: false,
        },
      ],
      order: [['createdAt', 'DESC']],
      limit: 10,
    });

    res.json({
      success: true,
      data: {
        ...product.toJSON(),
        reviews,
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products:
 *   post:
 *     summary: Create a product (Vendor/Admin only)
 *     tags: [Products]
 *     security:
 *       - bearerAuth: []
 */
router.post(
  '/',
  protect,
  authorize('admin', 'vendor'),
  [
    body('title').trim().notEmpty().withMessage('Product title is required'),
    body('description').notEmpty().withMessage('Description is required'),
    body('price').isFloat({ min: 0 }).withMessage('Valid price is required'),
    body('category').trim().notEmpty().withMessage('Category is required'),
    body('stock').isInt({ min: 0 }).withMessage('Valid stock count is required'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const productData = {
        ...req.body,
        vendor_id: req.user.id,
      };

      const product = await Product.create(productData);
      await cache.bust('products');
      logger.info(`Product created: ${product.title} (${product.id}) by ${req.user.email}`);

      res.status(201).json({
        success: true,
        data: product,
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * @swagger
 * /api/products/{id}:
 *   put:
 *     summary: Update product (Vendor/Admin only)
 *     tags: [Products]
 *     security:
 *       - bearerAuth: []
 */
router.put('/:id', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    if (req.user.role !== 'admin' && product.vendor_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized to update this product' });
    }

    await product.update(req.body);
    await cache.bust('products');

    res.json({
      success: true,
      data: product,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products/{id}:
 *   delete:
 *     summary: Delete product (Vendor/Admin only)
 *     tags: [Products]
 *     security:
 *       - bearerAuth: []
 */
router.delete('/:id', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    if (req.user.role !== 'admin' && product.vendor_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized to delete this product' });
    }

    await Review.destroy({ where: { product_id: req.params.id } });
    await product.destroy();
    await cache.bust('products');

    logger.info(`Product deleted: ${product.title} (${req.params.id})`);

    res.json({
      success: true,
      message: 'Product and associated reviews deleted successfully',
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/products/{id}/reviews:
 *   post:
 *     summary: Add a review to a product
 *     tags: [Products]
 *     security:
 *       - bearerAuth: []
 */
router.post(
  '/:id/reviews',
  protect,
  [
    body('rating').isInt({ min: 1, max: 5 }).withMessage('Rating must be between 1 and 5'),
    body('comment').trim().notEmpty().withMessage('Comment is required'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const product = await Product.findByPk(req.params.id);
      if (!product) {
        return res.status(404).json({ success: false, error: 'Product not found' });
      }

      const existingReview = await Review.findOne({
        where: { product_id: req.params.id, user_id: req.user.id },
      });

      if (existingReview) {
        return res.status(400).json({
          success: false,
          error: 'You have already reviewed this product',
        });
      }

      const review = await Review.create({
        product_id: req.params.id,
        user_id: req.user.id,
        userName: req.user.name,
        userAvatar: req.user.avatar || '',
        rating: req.body.rating,
        title: req.body.title || '',
        comment: req.body.comment,
        verifiedPurchase: true,
      });

      res.status(201).json({
        success: true,
        data: review,
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * @swagger
 * /api/products/{id}/reviews:
 *   get:
 *     summary: Get reviews for a product
 *     tags: [Products]
 */
router.get('/:id/reviews', async (req, res, next) => {
  try {
    const reviews = await Review.findAll({
      where: { product_id: req.params.id },
      include: [
        {
          model: User,
          as: 'user',
          attributes: ['id', 'name', 'avatar'],
          required: false,
        },
      ],
      order: [['createdAt', 'DESC']],
    });

    res.json({
      success: true,
      count: reviews.length,
      data: reviews,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
