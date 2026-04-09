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

  changePassword: (data: { new_password: string }) =>
    api.patch('/api/users/me/password', data),
};

// API Key API
export const apiKeyAPI = {
  // Shared API Keys
  shareAPIKey: (data: { provider: string; api_key: string; api_key_metadata?: string; selected_models?: string[] }, orgId?: number) =>
    api.post('/api/api-keys/share', data, { params: orgId ? { org_id: orgId } : undefined }),

  getMySharedAPIKeys: (orgId?: number) =>
    api.get('/api/api-keys/my-shared', { params: orgId ? { org_id: orgId } : undefined }),

  disableSharedAPIKey: (apiKeyId: number, orgId?: number) =>
    api.put(`/api/api-keys/disable/${apiKeyId}`, undefined, { params: orgId ? { org_id: orgId } : undefined }),

  enableSharedAPIKey: (apiKeyId: number, orgId?: number) =>
    api.put(`/api/api-keys/enable/${apiKeyId}`, undefined, { params: orgId ? { org_id: orgId } : undefined }),

  deleteSharedAPIKey: (apiKeyId: number, orgId?: number) =>
    api.delete(`/api/api-keys/${apiKeyId}`, { params: orgId ? { org_id: orgId } : undefined }),

  getSharedAPIKeyMetrics: (apiKeyId: number) =>
    api.get(`/api/api-keys/shared/${apiKeyId}/metrics`),

  getProviderModels: (provider: string) =>
    api.get(`/api/api-keys/providers/${provider}/models`),

  getProviders: () =>
    api.get('/api/api-keys/providers'),

  updateSharedAPIKey: (apiKeyId: number, data: { api_key?: string; selected_models: string[] }, orgId?: number) =>
    api.put(`/api/api-keys/shared/${apiKeyId}`, data, { params: orgId ? { org_id: orgId } : undefined }),

  // Unified API Keys
  createUnifiedAPIKey: (data: { api_key_name: string; description?: string; api_key_ids: number[] }, orgId?: number) =>
    api.post('/api/api-keys/unified', data, { params: orgId !== undefined ? { org_id: orgId } : undefined }),

  getMyUnifiedAPIKeys: (orgId?: number) =>
    api.get('/api/api-keys/my-unified', { params: orgId !== undefined ? { org_id: orgId } : undefined }),

  getMyUnifiedAPIKeysIncludeAutoCreated: (orgId?: number) =>
    api.get('/api/api-keys/my-unified', { params: { include_auto_created: true, ...(orgId !== undefined && { org_id: orgId }) } }),

  updateUnifiedAPIKey: (apiKeyId: number, data: { api_key_name?: string; description?: string; status?: string; daily_token_limit?: number | null }) =>
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
  getOverview: (params?: { target_date?: string; timezone?: string; unified_api_key_id?: number; org_id?: number }) => {
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
    org_id?: number;
  }) => {
    const paramsWithTimezone = {
      ...params,
      timezone: params?.timezone || getUserTimezone(),
    };
    return api.get('/api/usage/logs', { params: paramsWithTimezone });
  },
};

// Overview API
export const overviewAPI = {
  getSystemOverview: (params?: { days?: number; org_id?: number }) =>
    api.get('/api/usage/overview/system', { params })
};

// Model API
export const modelAPI = {
  getModels: (orgId?: number) =>
    api.get('/api/models', { params: orgId !== undefined ? { org_id: orgId } : undefined }),
};

// Admin API
export const adminAPI = {
  getUsers: (params?: { offset?: number; limit?: number; role_filter?: 'all' | 'admin' | 'user' }) =>
    api.get('/api/admin/users', { params }),

  grantAdmin: (userId: number) =>
    api.put(`/api/admin/users/${userId}/grant-admin`),

  revokeAdmin: (userId: number) =>
    api.put(`/api/admin/users/${userId}/revoke-admin`),

  createUser: (data: { email: string }) =>
    api.post('/api/admin/users/create', data),

  resetUserPassword: (userId: number) =>
    api.post(`/api/admin/users/${userId}/reset-password`),

  disableUser: (userId: number) =>
    api.put(`/api/admin/users/${userId}/disable`),

  enableUser: (userId: number) =>
    api.put(`/api/admin/users/${userId}/enable`),

  deleteUser: (userId: number) =>
    api.delete(`/api/admin/users/${userId}`),

  // Provider configuration API
  getProviders: (params?: { skip?: number; limit?: number; enabled_only?: boolean }) =>
    api.get('/api/admin/providers', { params }),

  getProvider: (id: number) =>
    api.get(`/api/admin/providers/${id}`),

  createProvider: (data: {
    provider_key: string;
    name: string;
    website: string;
    base_url: string;
    custom_llm_provider?: string;
    validation_endpoint?: string;
    logo?: File;
    models?: any[];
  }) => {
    const formData = new FormData();
    formData.append('provider_key', data.provider_key);
    formData.append('name', data.name);
    formData.append('website', data.website);
    formData.append('base_url', data.base_url);
    formData.append('custom_llm_provider', data.custom_llm_provider || 'openai');
    if (data.validation_endpoint) formData.append('validation_endpoint', data.validation_endpoint);
    if (data.logo) formData.append('logo', data.logo);
    if (data.models) formData.append('models_json', JSON.stringify(data.models));
    return api.post('/api/admin/providers', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  updateProvider: (id: number, data: {
    name?: string;
    website?: string;
    base_url?: string;
    custom_llm_provider?: string;
    validation_endpoint?: string;
    logo?: File;
    is_enabled?: boolean;
  }) => {
    const formData = new FormData();
    if (data.name !== undefined) formData.append('name', data.name);
    if (data.website !== undefined) formData.append('website', data.website);
    if (data.base_url !== undefined) formData.append('base_url', data.base_url);
    if (data.custom_llm_provider !== undefined) formData.append('custom_llm_provider', data.custom_llm_provider);
    if (data.validation_endpoint !== undefined) formData.append('validation_endpoint', data.validation_endpoint);
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

  // System Settings API
  getSystemSettings: () =>
    api.get('/api/admin/system-settings'),

  getSystemSetting: (key: string) =>
    api.get(`/api/admin/system-settings/${key}`),

  updateSystemSetting: (key: string, value: string) =>
    api.put(`/api/admin/system-settings/${key}`, { value }),

  getDefaultDailyTokenLimit: () =>
    api.get('/api/admin/default-daily-token-limit'),

  updateDefaultDailyTokenLimit: (value: string) =>
    api.put(`/api/admin/default-daily-token-limit`, { value }),

  // System Settings Config API
  getSystemSettingsConfig: () =>
    api.get('/api/admin/system-settings-config'),

  updateSystemSettingsConfig: (data: {
    default_daily_token_limit: number;
    max_claws_per_user: number;
    claw_apikey_daily_token_limit: number | null;
    // Archive config fields (optional)
    claws_archive_enabled?: boolean;
    claws_archive_auto_enabled?: boolean;
    claws_archive_schedule_daily?: string;
    claws_archive_schedule_interval?: number;
    claws_archive_retention_daily?: number;
    claws_archive_retention_interval?: number;
    claws_archive_max_manual?: number;
  }) => api.put('/api/admin/system-settings-config', data),

  // API Key Limit History API
  getAllLimitHistory: (params?: { page?: number; page_size?: number }) =>
    api.get('/api/admin/api-key-limit-history', { params }),

  getAPIKeyLimitHistory: (apiKeyId: number, params?: { page?: number; page_size?: number }) =>
    api.get(`/api/admin/api-keys/${apiKeyId}/limit-history`, { params }),

  // Operation Logs API
  getOperationLogs: (params?: {
    offset?: number;
    limit?: number;
    user_id?: number;
    operation_type?: string;
    resource_type?: string;
    start_time?: string;
    end_time?: string;
  }) => api.get('/api/admin/operation-logs', { params }),
};

// Model Config API - unified model catalog management
export const modelConfigAPI = {
  getModelCatalog: (params?: { provider_key?: string; enabled_only?: boolean }) =>
    api.get('/api/admin/model-catalog', { params }),

  overrideModel: (data: {
    provider_key: string;
    model_key: string;
    display_name?: string;
    description?: string;
    context_length?: string;
    max_output_length?: string;
    input_types?: string[];
    output_types?: string[];
    coding_score?: number;
    is_enabled?: boolean;
  }) => api.post('/api/admin/model-catalog/override', data),

  enableModel: (id: number) =>
    api.put(`/api/admin/providers/models/${id}/enable`),

  disableModel: (id: number) =>
    api.put(`/api/admin/providers/models/${id}/disable`),

  updateModel: (id: number, data: {
    display_name?: string;
    real_model?: string;
    description?: string;
    context_length?: string;
    max_output_length?: string;
    input_types?: string[];
    output_types?: string[];
    coding_score?: number;
  }) => api.put(`/api/admin/providers/models/${id}`, data),
};

// Global Model API
export const globalModelAPI = {
  list: () =>
    api.get('/api/admin/global-models'),

  create: (data: {
    model_key: string;
    display_name: string;
    description?: string;
    context_length: string;
    max_output_length: string;
    input_types?: string[];
    output_types?: string[];
    coding_score?: number;
    logo?: File;
  }) => {
    const formData = new FormData();
    formData.append('model_key', data.model_key);
    formData.append('display_name', data.display_name);
    if (data.description) formData.append('description', data.description);
    formData.append('context_length', data.context_length);
    formData.append('max_output_length', data.max_output_length);
    if (data.coding_score != null) formData.append('coding_score', String(data.coding_score));
    if (data.input_types && data.input_types.length > 0) formData.append('input_types_json', JSON.stringify(data.input_types));
    if (data.output_types && data.output_types.length > 0) formData.append('output_types_json', JSON.stringify(data.output_types));
    if (data.logo) formData.append('logo', data.logo);
    return api.post('/api/admin/global-models', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  update: (id: number, data: {
    display_name?: string;
    description?: string;
    context_length?: string;
    max_output_length?: string;
    input_types?: string[];
    output_types?: string[];
    coding_score?: number;
    logo?: File;
  }) => {
    const formData = new FormData();
    if (data.display_name != null) formData.append('display_name', data.display_name);
    if (data.description != null) formData.append('description', data.description);
    if (data.context_length != null) formData.append('context_length', data.context_length);
    if (data.max_output_length != null) formData.append('max_output_length', data.max_output_length);
    if (data.coding_score != null) formData.append('coding_score', String(data.coding_score));
    if (data.input_types) formData.append('input_types_json', JSON.stringify(data.input_types));
    if (data.output_types) formData.append('output_types_json', JSON.stringify(data.output_types));
    if (data.logo) formData.append('logo', data.logo);
    return api.put(`/api/admin/global-models/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  delete: (id: number) =>
    api.delete(`/api/admin/global-models/${id}`),
};

// Claw API
export const clawAPI = {
  getConfig: () => api.get('/api/claws/config'),

  createClaw: (data: { name: string; type: string; qq_bot_id: string; qq_bot_secret: string; brain_model?: string; chat_tool?: string }) =>
    api.post('/api/claws', data),

  getMyClaws: () =>
    api.get('/api/claws'),

  getClaw: (id: number) =>
    api.get(`/api/claws/${id}`),

  updateClaw: (id: number, data: { name: string }) =>
    api.put(`/api/claws/${id}`, data),

  deleteClaw: (id: number) =>
    api.delete(`/api/claws/${id}`),

  restartClaw: (id: number) =>
    api.post(`/api/claws/${id}/restart`),

  getLogs: (id: number, token: string): Promise<Response> =>
    fetch(`/api/claws/${id}/logs`, {
      headers: { Authorization: `Bearer ${token}` },
    }),

  larkInstall: (id: number, token: string): Promise<Response> =>
    fetch(`/api/claws/${id}/lark-install`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }),

  weixinLogin: (id: number, token: string): Promise<Response> =>
    fetch(`/api/claws/${id}/weixin-login`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }),

  setChatTool: (id: number, data: { chat_tool: string }, token: string): Promise<Response> =>
    fetch(`/api/claws/${id}/chat-tool`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }),

  getArchives: (id: number) =>
    api.get(`/api/claws/${id}/archives`),

  createArchive: (id: number) =>
    api.post(`/api/claws/${id}/archives`),

  restoreArchive: (id: number, timestamp: string) =>
    api.post(`/api/claws/${id}/archives/${timestamp}/restore`),

  deleteArchive: (id: number, timestamp: string) =>
    api.delete(`/api/claws/${id}/archives/${timestamp}`),
};

// Password Reset API
export const passwordResetAPI = {
  verifyToken: (token: string) =>
    api.post('/api/password-reset/verify', { token }),

  setPassword: (token: string, new_password: string) =>
    api.post('/api/password-reset/set-password', { token, new_password }),
};

// Organization API
export const organizationAPI = {
  createOrganization: (data: { name: string }) =>
    api.post('/api/organizations', data),

  getMyOrganizations: () =>
    api.get('/api/organizations/my'),

  listMembers: (orgId: number) =>
    api.get(`/api/organizations/${orgId}/members`),

  disableMember: (orgId: number, userId: number) =>
    api.put(`/api/organizations/${orgId}/members/${userId}/disable`),

  enableMember: (orgId: number, userId: number) =>
    api.put(`/api/organizations/${orgId}/members/${userId}/enable`),

  removeMember: (orgId: number, userId: number) =>
    api.delete(`/api/organizations/${orgId}/members/${userId}`),

  createInvite: (orgId: number) =>
    api.post(`/api/organizations/${orgId}/invite`),

  getInviteInfo: (token: string) =>
    api.get(`/api/organizations/invite/${token}`),

  acceptInvite: (token: string) =>
    api.post(`/api/organizations/invite/${token}/accept`),
};
