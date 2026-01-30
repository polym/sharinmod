'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { apiKeyAPI } from '@/lib/services';

interface DiscoveredAPIKey {
  id: number;
  provider: string;
  provider_username: string;
  total_uses: number;
  created_at: string;
  status: string;
}

export function APIKeyDiscovery() {
  const [apiKeys, setAPIKeys] = useState<DiscoveredAPIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [providerFilter, setProviderFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const loadAPIKeys = async (pageNum = 1, provider = 'all') => {
    try {
      const response = await apiKeyAPI.discoverAPIKeys({
        page: pageNum,
        limit: 10,
        provider: provider === 'all' ? undefined : provider,
      });

      if (pageNum === 1) {
        setAPIKeys(response.data.items);
      } else {
        setAPIKeys(prev => [...prev, ...response.data.items]);
      }

      setHasMore(response.data.items.length === 10);
    } catch (error: any) {
      toast({
        title: '错误',
        description: '加载API Key失败',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAPIKeys(1, providerFilter);
  }, [providerFilter]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadAPIKeys(nextPage, providerFilter);
  };

  const handleProviderFilter = (value: string) => {
    setProviderFilter(value);
    setPage(1);
  };

  const handleUseAPIKey = async (apiKeyId: number) => {
    // For now, redirect to chat page - in a real implementation,
    // you might want to create a unified API key first or handle this differently
    router.push(`/chat?apiKeyId=${apiKeyId}`);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>发现可用的API Keys</CardTitle>
          <CardDescription>
            浏览社区分享的API Keys，使用它们进行AI模型调用
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <Select value={providerFilter} onValueChange={handleProviderFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="选择供应商" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="bigmodel">bigmodel</SelectItem>
                <SelectItem value="z.ai">z.ai</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {loading && apiKeys.length === 0 ? (
            <div className="text-center py-8">加载中...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无可用的API Keys
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((apiKey) => (
                <Card key={apiKey.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">{apiKey.provider}</div>
                        <div className="text-sm text-gray-500">
                          提供者: {apiKey.provider_username}
                        </div>
                        <div className="text-sm text-gray-500">
                          使用次数: {apiKey.total_uses}
                        </div>
                        <div className="text-sm text-gray-500">
                          创建时间: {new Date(apiKey.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`px-2 py-1 rounded text-sm ${
                          apiKey.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {apiKey.status}
                        </div>
                        <Button
                          onClick={() => handleUseAPIKey(apiKey.id)}
                          disabled={apiKey.status !== 'active'}
                        >
                          使用
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {hasMore && (
                <div className="text-center pt-4">
                  <Button onClick={handleLoadMore} variant="outline">
                    加载更多
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}