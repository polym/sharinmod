import api from './api';

// Auth API
export const authAPI = {
  register: (data: { email: string; password: string }) =>
    api.post('/api/users/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/api/auth/login', data),

  getProfile: () => api.get('/api/users/me'),
};

// User API
export const userAPI = {
  updateProfile: (data: { name?: string; bio?: string }) =>
    api.patch('/api/users/me/profile', data),
};

// API Key API
export const apiKeyAPI = {
  // Shared API Keys
  shareAPIKey: (data: { provider: string; api_key: string; api_key_metadata?: string }) =>
    api.post('/api/api-keys/share', data),

  getMySharedAPIKeys: () => api.get('/api/api-keys/my-shared'),

  disableSharedAPIKey: (apiKeyId: number) =>
    api.put(`/api/api-keys/disable/${apiKeyId}`),

  enableSharedAPIKey: (apiKeyId: number) =>
    api.put(`/api/api-keys/enable/${apiKeyId}`),

  deleteSharedAPIKey: (apiKeyId: number) =>
    api.delete(`/api/api-keys/${apiKeyId}`),

  getSharedAPIKeyMetrics: (apiKeyId: number) =>
    api.get(`/api/api-keys/shared/${apiKeyId}/metrics`),

  // Unified API Keys
  createUnifiedAPIKey: (data: { api_key_name: string; description?: string; api_key_ids: number[] }) =>
    api.post('/api/api-keys/unified', data),

  getMyUnifiedAPIKeys: () => api.get('/api/api-keys/my-unified'),

  updateUnifiedAPIKey: (apiKeyId: number, data: { api_key_name?: string; description?: string; status?: string }) =>
    api.put(`/api/api-keys/unified/${apiKeyId}`, data),

  blockUnifiedAPIKey: (apiKeyId: number) =>
    api.put(`/api/api-keys/unified/${apiKeyId}/block`),

  unblockUnifiedAPIKey: (apiKeyId: number) =>
    api.put(`/api/api-keys/unified/${apiKeyId}/unblock`), // Note: Backend support required

  deleteUnifiedAPIKey: (apiKeyId: number) =>
    api.delete(`/api/api-keys/unified/${apiKeyId}`),

  regenerateUnifiedAPIKey: (apiKeyId: number) =>
    api.post(`/api/api-keys/unified/${apiKeyId}/regenerate`),

  // API Key discovery
  discoverAPIKeys: (params?: { page?: number; limit?: number; provider?: string }) =>
    api.get('/api/api-keys/discover', { params }),

  // API Key usage history
  getUsageHistory: (params?: { page?: number; limit?: number }) =>
    api.get('/api/users/me/api-key-usage', { params }),

  // API Key consumption (proxy)
  consumeChatCompletion: (data: {
    model: string;
    messages: Array<{ role: string; content: string }>;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }, unifiedAPIKey: string) =>
    api.post('/api/proxy/chat/completions', data, {
      headers: {
        Authorization: `Bearer ${unifiedAPIKey}`,
      },
    }),
};