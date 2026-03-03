/**
 * Provider configuration
 * Maps provider codes to brand names and logos
 */

export type ProviderCode = 'bigmodel' | 'z.ai' | 'volcengine' | 'moonshot' | 'minimax' | 'openrouter' | 'bailian';

export interface ProviderConfig {
  code: ProviderCode;
  brandName: string;
  logoPath: string;
}

export const PROVIDERS: Record<ProviderCode, ProviderConfig> = {
  bigmodel: {
    code: 'bigmodel',
    brandName: '智谱 AI',
    logoPath: '/providers/bigmodel-logo.png',
  },
  'z.ai': {
    code: 'z.ai',
    brandName: 'Z.AI',
    logoPath: '/providers/zai-logo.png',
  },
  volcengine: {
    code: 'volcengine',
    brandName: '火山引擎',
    logoPath: '/providers/volcengine-logo.png',
  },
  moonshot: {
    code: 'moonshot',
    brandName: '月之暗面',
    logoPath: '/providers/moonshot-logo.png',
  },
  minimax: {
    code: 'minimax',
    brandName: 'MiniMax',
    logoPath: '/providers/minimax-logo.png',
  },
  openrouter: {
    code: 'openrouter',
    brandName: 'OpenRouter',
    logoPath: '/providers/openrouter-logo.png',
  },
  bailian: {
    code: 'bailian',
    brandName: '阿里云百炼',
    logoPath: '/providers/bailian-logo.png',
  },
};

export const PROVIDER_LIST = Object.values(PROVIDERS);

/**
 * Get provider config by code
 */
export function getProvider(code: string): ProviderConfig | undefined {
  return PROVIDERS[code as ProviderCode];
}

/**
 * Get provider brand name by code
 */
export function getProviderBrandName(code: string): string {
  return getProvider(code)?.brandName || code;
}

/**
 * Get provider logo path by code
 * Falls back to /providers/{code}-logo.png for unregistered providers
 */
export function getProviderLogo(code: string): string {
  return getProvider(code)?.logoPath || `/providers/${code}-logo.png`;
}

/**
 * Model logo map - maps model name prefixes to local logo paths
 */
export const MODEL_LOGO_MAP: Record<string, string> = {
  'kimi': '/models/kimi.png',
  'doubao': '/models/doubao.png',
  'deepseek': '/models/deepseek.png',
  'glm': '/models/glm.png',
  'minimax': '/models/minimax.png',
};

/**
 * Get model logo path by model name
 * @param modelName - Model name (e.g., "glm-4.7")
 * @returns Path to model logo image (e.g., "/models/glm-4.7.png")
 */
export function getModelLogo(modelName: string): string {
  // Check if model name prefix matches MODEL_LOGO_MAP
  const lowerModelName = modelName.toLowerCase();
  for (const [prefix, path] of Object.entries(MODEL_LOGO_MAP)) {
    if (lowerModelName.startsWith(prefix)) {
      return path;
    }
  }
  // Fallback to model-specific path
  return `/models/${modelName}.png`;
}

/**
 * Built-in provider default connection config
 * Used to pre-fill edit form when db values are null (legacy records before 20260226 migration)
 */
export interface ProviderConnectionDefaults {
  base_url: string;
  custom_llm_provider: string;
}

export const BUILTIN_PROVIDER_DEFAULTS: Partial<Record<string, ProviderConnectionDefaults>> = {
  bigmodel: {
    base_url: 'https://open.bigmodel.cn/api/paas/v4',
    custom_llm_provider: 'anthropic',
  },
  'z.ai': {
    base_url: 'https://api.z.ai/v1',
    custom_llm_provider: 'anthropic',
  },
  volcengine: {
    base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    custom_llm_provider: 'anthropic',
  },
  moonshot: {
    base_url: 'https://api.moonshot.cn/v1',
    custom_llm_provider: 'anthropic',
  },
  minimax: {
    base_url: 'https://api.minimax.chat/v1',
    custom_llm_provider: 'anthropic',
  },
  openrouter: {
    base_url: 'https://openrouter.ai/api/v1',
    custom_llm_provider: 'openrouter',
  },
};

/**
 * Get provider default connection config by provider_key
 */
export function getProviderDefaults(providerKey: string): ProviderConnectionDefaults | undefined {
  return BUILTIN_PROVIDER_DEFAULTS[providerKey];
}

/**
 * Provider info with supported models
 */
export const PROVIDER_INFO: Record<ProviderCode, { supported_models: string[] }> = {
  bigmodel: {
    supported_models: ['glm-5', 'glm-4.7', 'glm-4.6', 'glm-4.5-air'],
  },
  'z.ai': {
    supported_models: ['glm-5', 'glm-4.7', 'glm-4.6', 'glm-4.5-air'],
  },
  volcengine: {
    supported_models: ['doubao-seed-code', 'kimi-k2.5', 'kimi-k2', 'glm-4.7', 'deepseek-v3.2'],
  },
  moonshot: {
    supported_models: ['kimi-k2.5'],
  },
  minimax: {
    supported_models: ['minimax-m2.1'],
  },
  openrouter: {
    supported_models: ['pony-alpha'],
  },
};
