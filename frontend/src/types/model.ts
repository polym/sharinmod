/**
 * 模型相关的类型定义
 */

export interface SharedBy {
  user_id: number;
  name?: string;
  avatar_url?: string;
}

export interface ProviderInfo {
  code: string;
  logo_path: string;
}

export interface ModelInfo {
  display_name: string;
  model_name: string;
  provider: string;
  description: string;
  input_types: string[];
  output_types: string[];
  context_length: string;
  max_output_length: string;
  available_subscriptions: number;
  shared_by: SharedBy[];
  used_tokens?: number;
  coding_score?: number | null;
  providers?: ProviderInfo[];
  subscription_platform_count?: number;
}
