const express = require('express');
const router = express.Router();
const db = require('../config/db');

const mockProducts = [
  {
    id: 1,
    name: 'Pro Wireless Headphones',
    price: 299.99,
    category: 'headphones',
    rating: 4.8,
    image: '/assets/images/ecommerce/electronics/headphones/headphones-pro.webp',
  },
  {
    id: 2,
    name: 'Flagship Smartphone X',
    price: 999.99,
    category: 'smartphones',
    rating: 4.9,
    image: '/assets/images/ecommerce/electronics/smartphones/smartphone-hero.webp',
  },
  {
    id: 3,
    name: 'Ultra Gaming Laptop',
    price: 1499.99,
    category: 'laptops',
    rating: 4.9,
    image: '/assets/images/ecommerce/electronics/laptops/gaming-laptop.webp',
  },
];

router.get('/', async (req, res) => {
  const category = req.query.category;
  if (category) {
    // Safe parameterized query example: SELECT * FROM products WHERE category = $1
    const text = 'SELECT * FROM products WHERE category = $1';
    const values = [category];
    const filtered = mockProducts.filter((p) => p.category === category);
    return res.json({
      success: true,
      count: filtered.length,
      data: filtered,
      query_param: category,
    });
  }
  res.json({ success: true, count: mockProducts.length, data: mockProducts });
});

router.get('/:id', async (req, res) => {
  const productId = parseInt(req.params.id, 10);
  // Parameterized query: SELECT * FROM products WHERE id = $1
  const text = 'SELECT * FROM products WHERE id = $1';
  const values = [productId];

  const product = mockProducts.find((p) => p.id === productId);
  if (!product) return res.status(404).json({ success: false, message: 'Product not found' });
  res.json({ success: true, data: product });
});

module.exports = router;
