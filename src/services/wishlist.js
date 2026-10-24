import api from './api';

const wishlistAPI = {
  get: () => api.get('/wishlist'),
  // POST is an idempotent add (a retry can no longer delete the entry);
  // removal is the DELETE below.
  add: (productId) => api.post('/wishlist', { product_id: productId }),
  remove: (productId) => api.delete(`/wishlist/${productId}`),
};

export default wishlistAPI;
