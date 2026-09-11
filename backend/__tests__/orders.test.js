import Order from '../models/Order.js';

describe('Order Model Validation & Calculations', () => {
  it('should build an order instance with correct defaults and fields', () => {
    const order = Order.build({
      user_id: 1,
      orderNumber: 'ORD-20260831-TEST1',
      items: [
        {
          product_id: 7,
          title: 'Sample Product',
          price: 50.0,
          quantity: 2,
        },
      ],
      shippingAddress: {
        fullName: 'Test User',
        street: '123 Market St',
        city: 'New York',
        state: 'NY',
        zipCode: '10001',
        country: 'USA',
      },
      paymentMethod: 'stripe',
      itemsPrice: 100.0,
      taxPrice: 8.0,
      shippingPrice: 0.0,
      totalPrice: 108.0,
      status: 'pending',
    });

    expect(order.orderNumber).toBe('ORD-20260831-TEST1');
    expect(order.totalPrice).toBe(108.0);
    expect(order.status).toBe('pending');
    expect(order.isPaid).toBe(false);
    expect(order.currency).toBe('USD');
    expect(order.items).toHaveLength(1);
  });

  it('should apply model defaults when optional fields are omitted', () => {
    const order = Order.build({
      orderNumber: 'ORD-20260831-TEST2',
      items: [],
      shippingAddress: { fullName: 'A', country: 'PK' },
      paymentMethod: 'paypal',
    });

    expect(order.isPaid).toBe(false);
    expect(order.isDelivered).toBe(false);
    expect(order.status).toBe('pending');
    expect(order.taxPrice).toBe(0);
    expect(order.itemsPrice).toBe(0);
  });

  it('should reject an invalid payment method on validation', async () => {
    const order = Order.build({
      orderNumber: 'ORD-20260831-TEST3',
      items: [],
      shippingAddress: { fullName: 'A', country: 'PK' },
      paymentMethod: 'bitcoin',
    });

    await expect(order.validate()).rejects.toThrow('Invalid payment method');
  });
});