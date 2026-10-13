import api from './api';

const vehicleApi = {
  async list(filters = {}, { signal } = {}) {
    const { data } = await api.get('/vehicles', { params: filters, signal });
    return data.data;
  },
  async getBySlug(slug, { signal } = {}) {
    const { data } = await api.get(`/vehicles/${encodeURIComponent(slug)}`, { signal });
    return data.data;
  },
  async submitInquiry(payload, { signal } = {}) {
    const { data } = await api.post('/inquiries', payload, { signal });
    return data.data;
  },
};

export default vehicleApi;
