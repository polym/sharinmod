'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { apiKeyAPI } from '@/lib/services';

interface UsageRecord {
  id: number;
  api_key_id: number;
  unified_api_key_id?: number;
  endpoint: string;
  method: string;
  status_code: number;
  created_at: string;
  response_time_ms?: number;
  vendor?: string;
}

export function APIKeyUsage() {
  const [usage, setUsage] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const loadUsage = async (pageNum = 1) => {
    try {
      const response = await apiKeyAPI.getUsageHistory({
        page: pageNum,
        limit: 20,
      });

      if (pageNum === 1) {
        setUsage(response.data.items);
      } else {
        setUsage(prev => [...prev, ...response.data.items]);
      }

      setHasMore(response.data.items.length === 20);
    } catch (error) {
      console.error('Failed to load usage:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsage();
  }, []);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadUsage(nextPage);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>API Key使用历史</CardTitle>
        <CardDescription>
          查看您的API Key使用记录和API调用历史
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading && usage.length === 0 ? (
          <div className="text-center py-8">加载中...</div>
        ) : usage.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无使用记录
          </div>
        ) : (
          <div className="space-y-4">
            {usage.map((record) => (
              <div key={record.id} className="flex items-center justify-between p-4 border rounded">
                <div className="space-y-1">
                  <div className="font-medium">
                    {record.method} {record.endpoint}
                  </div>
                  <div className="text-sm text-gray-500">
                    {record.vendor && `供应商: ${record.vendor}`}
                    {record.unified_api_key_id && ` | 统一API Key ID: ${record.unified_api_key_id}`}
                  </div>
                  <div className="text-sm text-gray-500">
                    时间: {new Date(record.created_at).toLocaleString()}
                  </div>
                  {record.response_time_ms && (
                    <div className="text-sm text-gray-500">
                      响应时间: {record.response_time_ms}ms
                    </div>
                  )}
                </div>
                <div className={`px-2 py-1 rounded text-sm ${
                  record.status_code >= 200 && record.status_code < 300
                    ? 'bg-green-100 text-green-800'
                    : record.status_code >= 400
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {record.status_code}
                </div>
              </div>
            ))}

            {hasMore && (
              <div className="text-center pt-4">
                <button
                  onClick={handleLoadMore}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  加载更多
                </button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}