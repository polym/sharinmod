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

// Token API
export const tokenAPI = {
  // Shared tokens
  shareToken: (data: { vendor: string; token: string; metadata?: string }) =>
    api.post('/api/tokens/share', data),

  getMySharedTokens: () => api.get('/api/tokens/my-shared'),

  disableSharedToken: (tokenId: number) =>
    api.put(`/api/tokens/disable/${tokenId}`),

  enableSharedToken: (tokenId: number) =>
    api.put(`/api/tokens/enable/${tokenId}`),

  deleteSharedToken: (tokenId: number) =>
    api.delete(`/api/tokens/${tokenId}`),

  // Unified tokens
  createUnifiedToken: (data: { token_name: string; description?: string; token_ids: number[] }) =>
    api.post('/api/tokens/unified', data),

  getMyUnifiedTokens: () => api.get('/api/tokens/my-unified'),

  blockUnifiedToken: (tokenId: number) =>
    api.put(`/api/tokens/unified/${tokenId}/block`),

  deleteUnifiedToken: (tokenId: number) =>
    api.delete(`/api/tokens/unified/${tokenId}`),

  regenerateUnifiedToken: (tokenId: number) =>
    api.post(`/api/tokens/unified/${tokenId}/regenerate`),

  // Token discovery
  discoverTokens: (params?: { page?: number; limit?: number; vendor?: string }) =>
    api.get('/api/tokens/discover', { params }),

  // Token usage history
  getUsageHistory: (params?: { page?: number; limit?: number }) =>
    api.get('/api/users/me/usage-history', { params }),

  // Token consumption (proxy)
  consumeChatCompletion: (data: {
    model: string;
    messages: Array<{ role: string; content: string }>;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }, unifiedToken: string) =>
    api.post('/api/proxy/chat/completions', data, {
      headers: {
        Authorization: `Bearer ${unifiedToken}`,
      },
    }),
};