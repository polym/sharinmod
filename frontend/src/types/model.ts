/**
 * 模型相关的类型定义
 */

export interface SharedBy {
  user_id: number;
  name?: string;
  avatar_url?: string;
}

export interface ModelInfo {
  display_name: string;
  model_name: string;
  provider: string;
  description: string;
  input_type: string;
  output_type: string;
  context_length: string;
  max_output_length: string;
  available_subscriptions: number;
  shared_by: SharedBy[];
}
