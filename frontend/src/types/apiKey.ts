export interface SharedAPIKey {
  id: number;
  provider: string;
  status: string;
  created_at: string;
  total_uses: number;
  api_key_metadata?: string;
}
