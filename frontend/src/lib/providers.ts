/**
 * Provider configuration
 * Maps provider codes to brand names and logos
 */

export type ProviderCode = 'bigmodel' | 'z.ai' | 'volcengine';

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
 */
export function getProviderLogo(code: string): string {
  return getProvider(code)?.logoPath || '/providers/default-logo.png';
}

/**
 * Get model logo path by model name
 * @param modelName - Model name (e.g., "glm-4.7")
 * @returns Path to model logo image (e.g., "/models/glm-4.7.png")
 */
export function getModelLogo(modelName: string): string {
  return `/models/${modelName}.png`;
}

/**
 * Provider info with supported models
 */
export const PROVIDER_INFO: Record<ProviderCode, { supported_models: string[] }> = {
  bigmodel: {
    supported_models: ['glm-4.7', 'glm-4.6', 'glm-4.5-air'],
  },
  'z.ai': {
    supported_models: ['glm-4.7', 'glm-4.6', 'glm-4.5-air'],
  },
  volcengine: {
    supported_models: ['doubao-seed-code', 'kimi-k2.5', 'kimi-k2', 'glm-4.7', 'deepseek-v3.2'],
  },
};
