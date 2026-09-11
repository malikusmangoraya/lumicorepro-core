import api from './api';

const settingsApi = {
  status: () => api.get('/settings/status').then((r) => r.data?.data),
  public: () => api.get('/settings/public').then((r) => r.data?.data),
  getSystem: () => api.get('/settings/system').then((r) => r.data?.data),
  updateSystem: (payload) => api.put('/settings/system', payload).then((r) => r.data?.data),
  setup: (payload) => api.post('/settings/setup', payload).then((r) => r.data?.data),
};

export default settingsApi;