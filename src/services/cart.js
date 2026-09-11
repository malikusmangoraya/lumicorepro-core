import api from './api';

const cartAPI = {
  get: () => api.get('/cart'),
  addItem: (productId, quantity = 1, options = {}) =>
    api.post('/cart/items', { productId, quantity, ...options }),
  updateItem: (itemId, quantity) => api.put(`/cart/items/${itemId}`, { quantity }),
  removeItem: (itemId) => api.delete(`/cart/items/${itemId}`),
  clear: () => api.delete('/cart'),
  getCount: () => api.get('/cart/count'),
};

export default cartAPI;
