/**
 * LumicorePro — Organization (multi-tenant) service.
 * Wraps all /api/orgs calls behind the central api.js axios instance.
 */
import api from './api';

const orgService = {
  list: () => api.get('/orgs'),
  create: (name) => api.post('/orgs', { name }),
  current: () => api.get('/orgs/current'),
  select: (orgId) => api.post(`/orgs/${orgId}/select`),
  update: (orgId, name) => api.put(`/orgs/${orgId}`, { name }),
  remove: (orgId) => api.delete(`/orgs/${orgId}`),

  roles: (orgId) => api.get(`/orgs/${orgId}/roles`),
  permissions: () => api.get('/orgs/permissions'),

  members: (orgId) => api.get(`/orgs/${orgId}/members`),
  invite: (orgId, email, role = 'member') => api.post(`/orgs/${orgId}/members`, { email, role }),
  updateMember: (orgId, userId, data) => api.put(`/orgs/${orgId}/members/${userId}`, data),
  removeMember: (orgId, userId) => api.delete(`/orgs/${orgId}/members/${userId}`),
};

export default orgService;