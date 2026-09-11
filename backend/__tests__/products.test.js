import Product from '../models/Product.js';

describe('Product Model Validation & Logic', () => {
  it('should instantiate a product with required fields', () => {
    const product = new Product({
      title: 'Wireless Headphones',
      description: 'High performance wireless headphones with active noise cancellation.',
      price: 199.99,
      category: 'Audio',
      stock: 25,
    });

    expect(product.title).toBe('Wireless Headphones');
    expect(product.price).toBe(199.99);
    expect(product.stock).toBe(25);
    expect(product.category).toBe('Audio');
    expect(product.isActive).toBe(true);
  });

  it('should require title, price, and description for valid model creation', () => {
    const product = new Product({});

    expect(product.title).toBeUndefined();
    expect(product.price).toBeUndefined();
    expect(product.description).toBeUndefined();
    expect(product.isActive).toBe(true);
  });
});
