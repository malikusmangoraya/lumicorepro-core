export const orderSteps = ['Order Received', 'Being Prepared', 'Ready for Pickup', 'Delivered'];

export const orders = [
  {
    id: '#ORD-8391',
    items: 'Chicken Biryani, Garlic Naan ×2, Raita',
    total: 'Rs 1,640',
    eta: '10 min',
    step: 2,
    payment: 'Card •••• 4021',
  },
  {
    id: '#ORD-8390',
    items: 'Beef Seekh Kebab Roll ×2, Fries',
    total: 'Rs 980',
    eta: '25 min',
    step: 1,
    payment: 'Cash on Delivery',
  },
  {
    id: '#ORD-8389',
    items: 'Butter Chicken, Tandoori Roti ×4',
    total: 'Rs 1,250',
    eta: 'Delivered',
    step: 3,
    payment: 'Card •••• 1129',
  },
  {
    id: '#ORD-8388',
    items: 'Palak Paneer, Jeera Rice, Gulab Jamun',
    total: 'Rs 1,385',
    eta: 'Delivered',
    step: 3,
    payment: 'JazzCash',
  },
];

export const deliveryPromise = [
  { icon: 'Fresh', label: 'Cooked to order', desc: 'Prepared only after you place the order' },
  { icon: 'Fast', label: '45-min delivery', desc: 'Hot and fresh at your doorstep' },
  { icon: 'Safe', label: 'Sealed packaging', desc: 'Tamper-proof, eco-friendly boxes' },
];
