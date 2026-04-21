export interface SharedAPIKey {
  id: number;
  provider: string;
  status: string;
  created_at: string;
  total_uses: number;
  api_key_metadata?: string;
  // Extended provider info fields
  supported_models?: string[];
  provider_website?: string;
  provider_display_name?: string;
  provider_logo_path?: string;
  // Rate limit fields
  rate_limit_reset_at?: string;
  rate_limit_models_backup?: string;
}

export interface ChartDataPoint {
  date: string;
  value: number;
}

export interface SharedAPIKeyMetrics {
  total_tokens: number;
  total_duration_days: number;
  total_requests: number;
  chart_data: ChartDataPoint[];
}

export interface UpdateSharedAPIKeyRequest {
  api_key?: string;
  selected_models: string[];
}
