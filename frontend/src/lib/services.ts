import api from './api';

// Helper function to get user's timezone
export const getUserTimezone = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai';
};

// Auth API
export const authAPI = {
  login: (data: { email: string; password: string }) =>
    api.post('/api/auth/login', data),

  getProfile: () => api.get('/api/users/me'),

  // OAuth 相关方法
  getOAuthProviders: () => api.get('/api/oauth/providers'),
};

// User API
export const userAPI = {
  updateProfile: (data: { name?: string; bio?: string }) =>
    api.patch('/api/users/me/profile', data),
};

// API Key API
export const apiKeyAPI = {
  // Shared API Keys
  shareAPIKey: (data: { provider: string; api_key: string; api_key_metadata?: string; selected_models?: string[] }) =>
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

  getProviderModels: (provider: string) =>
    api.get(`/api/api-keys/providers/${provider}/models`),

  getProviders: () =>
    api.get('/api/api-keys/providers'),

  updateSharedAPIKey: (apiKeyId: number, data: { api_key?: string; selected_models: string[] }) =>
    api.put(`/api/api-keys/shared/${apiKeyId}`, data),

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

// Usage API
export const usageAPI = {
  getOverview: (params?: { target_date?: string; timezone?: string; unified_api_key_id?: number }) => {
    const paramsWithTimezone = {
      ...params,
      timezone: params?.timezone || getUserTimezone(),
    };
    return api.get('/api/usage/overview', { params: paramsWithTimezone });
  },

  getLogs: (params?: {
    page?: number;
    page_size?: number;
    start_date?: string;
    end_date?: string;
    status?: string;
    timezone?: string;
    unified_api_key_id?: number;
  }) => {
    const paramsWithTimezone = {
      ...params,
      timezone: params?.timezone || getUserTimezone(),
    };
    return api.get('/api/usage/logs', { params: paramsWithTimezone });
  },
};

// Model API
export const modelAPI = {
  getModels: () => api.get('/api/models'),
};

// Admin API
export const adminAPI = {
  getUsers: (params?: { offset?: number; limit?: number; role_filter?: 'all' | 'admin' | 'user' }) =>
    api.get('/api/admin/users', { params }),

  grantAdmin: (userId: number) =>
    api.put(`/api/admin/users/${userId}/grant-admin`),

  revokeAdmin: (userId: number) =>
    api.put(`/api/admin/users/${userId}/revoke-admin`),

  // Provider configuration API
  getProviders: (params?: { skip?: number; limit?: number; enabled_only?: boolean }) =>
    api.get('/api/admin/providers', { params }),

  getProvider: (id: number) =>
    api.get(`/api/admin/providers/${id}`),

  createProvider: (data: {
    provider_key: string;
    name: string;
    website: string;
    logo?: File;
    models?: any[];
  }) => {
    const formData = new FormData();
    formData.append('provider_key', data.provider_key);
    formData.append('name', data.name);
    formData.append('website', data.website);
    if (data.logo) formData.append('logo', data.logo);
    if (data.models) formData.append('models_json', JSON.stringify(data.models));
    return api.post('/api/admin/providers', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  updateProvider: (id: number, data: {
    name?: string;
    website?: string;
    logo?: File;
    is_enabled?: boolean;
  }) => {
    const formData = new FormData();
    if (data.name !== undefined) formData.append('name', data.name);
    if (data.website !== undefined) formData.append('website', data.website);
    if (data.is_enabled !== undefined) formData.append('is_enabled', String(data.is_enabled));
    if (data.logo) formData.append('logo', data.logo);
    return api.put(`/api/admin/providers/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  deleteProvider: (id: number) =>
    api.delete(`/api/admin/providers/${id}`),

  enableProvider: (id: number) =>
    api.put(`/api/admin/providers/${id}/enable`),

  disableProvider: (id: number) =>
    api.put(`/api/admin/providers/${id}/disable`),

  updateProviderModels: (id: number, models: any[]) =>
    api.put(`/api/admin/providers/${id}/models`, { models }),

  enableProviderModel: (id: number) =>
    api.put(`/api/admin/providers/models/${id}/enable`),

  disableProviderModel: (id: number) =>
    api.put(`/api/admin/providers/models/${id}/disable`),

  // Model CRUD API
  createModel: (providerId: number, data: {
    model_key: string;
    display_name: string;
    description?: string;
    context_length: string;
    max_output_length: string;
    input_types?: string[];
    output_types?: string[];
    coding_score?: number;
  }) =>
    api.post(`/api/admin/providers/${providerId}/models`, data),

  updateModel: (modelId: number, data: {
    display_name?: string;
    description?: string;
    context_length?: string;
    max_output_length?: string;
    input_types?: string[];
    output_types?: string[];
    coding_score?: number;
  }) =>
    api.put(`/api/admin/providers/models/${modelId}`, data),

  deleteModel: (modelId: number) =>
    api.delete(`/api/admin/providers/models/${modelId}`),
};
