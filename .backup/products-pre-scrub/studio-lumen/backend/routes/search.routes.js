import express from 'express';
import { Op } from 'sequelize';
import Product from '../models/Product.js';
import User from '../models/User.js';
import cache from '../services/cache/cache.service.js';

const router = express.Router();

/**
 * @swagger
 * /api/search:
 *   get:
 *     summary: Global search across entities (products, categories, users)
 *     tags: [Search]
 */
router.get('/', async (req, res, next) => {
  try {
    const { q, type = 'all', limit = 10, category } = req.query;

    if (!q || q.trim() === '') {
      return res.status(400).json({ success: false, error: 'Query string q is required' });
    }

    const searchQuery = q.trim();
    const searchLimit = parseInt(limit, 10) || 10;

    // Cache search results for 10 min (fast-moving query space is bounded by inventory size)
    const cacheKey = `search:${type}:${searchQuery.slice(0, 50)}:${searchLimit}:${category || ''}`;
    const cached = await cache.get('search', cacheKey);
    if (cached)
      return res.json({ success: true, query: searchQuery, data: cached, meta: { cached: true } });

    const results = {};

    // 1. Search Products
    if (type === 'all' || type === 'products') {
      const productWhere = {
        isActive: true,
        [Op.or]: [
          { title: { [Op.iLike]: `%${searchQuery}%` } },
          { description: { [Op.iLike]: `%${searchQuery}%` } },
          { category: { [Op.iLike]: `%${searchQuery}%` } },
        ],
      };

      if (category && category !== 'all') {
        productWhere.category = { [Op.iLike]: category };
      }

      results.products = await Product.findAll({
        attributes: [
          'id',
          'title',
          'slug',
          'price',
          'comparePrice',
          'thumbnail',
          'category',
          'rating',
          'stock',
        ],
        where: productWhere,
        limit: searchLimit,
      });
    }

    // 2. Search Categories (distinct values from products table)
    if (type === 'all' || type === 'categories') {
      const categoryRows = await Product.findAll({
        attributes: ['category'],
        where: {
          isActive: true,
          category: { [Op.iLike]: `%${searchQuery}%` },
        },
        group: ['category'],
        raw: true,
      });
      results.categories = categoryRows.map((r) => r.category);
    }

    // 3. Search Users (only if authorization header present)
    if ((type === 'all' || type === 'users') && req.headers.authorization) {
      try {
        results.users = await User.findAll({
          attributes: ['id', 'name', 'email', 'role', 'avatar'],
          where: {
            [Op.or]: [
              { name: { [Op.iLike]: `%${searchQuery}%` } },
              { email: { [Op.iLike]: `%${searchQuery}%` } },
            ],
          },
          limit: 5,
        });
      } catch (_e) {
        // Skip user search if error
      }
    }

    await cache.set('search', cacheKey, results, cache.TTL.SEARCH);

    res.json({
      success: true,
      query: searchQuery,
      data: results,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/search/autocomplete:
 *   get:
 *     summary: Quick autocomplete suggestions for searchbar
 *     tags: [Search]
 */
router.get('/autocomplete', async (req, res, next) => {
  try {
    const { q } = req.query;
    if (!q || q.trim().length < 2) {
      return res.json({ success: true, data: [] });
    }

    const searchQuery = q.trim();

    const products = await Product.findAll({
      attributes: ['id', 'title', 'slug', 'price', 'thumbnail', 'category'],
      where: {
        isActive: true,
        title: { [Op.iLike]: `%${searchQuery}%` },
      },
      limit: 6,
    });

    const suggestions = products.map((p) => ({
      id: p.id,
      title: p.title,
      slug: p.slug,
      price: p.price,
      thumbnail: p.thumbnail,
      category: p.category,
      type: 'product',
    }));

    res.json({
      success: true,
      data: suggestions,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/search/trending:
 *   get:
 *     summary: Get popular/trending search keywords and top categories
 *     tags: [Search]
 */
router.get('/trending', async (req, res, next) => {
  try {
    const categoryRows = await Product.findAll({
      attributes: ['category'],
      where: { isActive: true },
      group: ['category'],
      raw: true,
    });

    const topKeywords = [
      'Wireless Headphones',
      'Smart Watch',
      'Mechanical Keyboard',
      'Gaming Mouse',
      'Laptop Stand',
      'USB-C Hub',
    ];

    res.json({
      success: true,
      data: {
        keywords: topKeywords,
        categories: categoryRows.map((r) => r.category).slice(0, 8),
      },
    });
  } catch (error) {
    next(error);
  }
});

export default router;
