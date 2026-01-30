'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { tokenAPI } from '@/lib/services';

interface DiscoveredToken {
  id: number;
  vendor: string;
  provider_username: string;
  total_uses: number;
  created_at: string;
  status: string;
}

export function TokenDiscovery() {
  const [tokens, setTokens] = useState<DiscoveredToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [vendorFilter, setVendorFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const loadTokens = async (pageNum = 1, vendor = 'all') => {
    try {
      const response = await tokenAPI.discoverTokens({
        page: pageNum,
        limit: 10,
        vendor: vendor === 'all' ? undefined : vendor,
      });

      if (pageNum === 1) {
        setTokens(response.data.items);
      } else {
        setTokens(prev => [...prev, ...response.data.items]);
      }

      setHasMore(response.data.items.length === 10);
    } catch (error: any) {
      toast({
        title: '错误',
        description: '加载token失败',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTokens(1, vendorFilter);
  }, [vendorFilter]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadTokens(nextPage, vendorFilter);
  };

  const handleVendorFilter = (value: string) => {
    setVendorFilter(value);
    setPage(1);
  };

  const handleUseToken = async (tokenId: number) => {
    // For now, redirect to chat page - in a real implementation,
    // you might want to create a unified token first or handle this differently
    router.push(`/chat?tokenId=${tokenId}`);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>发现可用的Tokens</CardTitle>
          <CardDescription>
            浏览社区分享的API tokens，使用它们进行AI模型调用
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <Select value={vendorFilter} onValueChange={handleVendorFilter}>
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

          {loading && tokens.length === 0 ? (
            <div className="text-center py-8">加载中...</div>
          ) : tokens.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无可用的tokens
            </div>
          ) : (
            <div className="space-y-4">
              {tokens.map((token) => (
                <Card key={token.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">{token.vendor}</div>
                        <div className="text-sm text-gray-500">
                          提供者: {token.provider_username}
                        </div>
                        <div className="text-sm text-gray-500">
                          使用次数: {token.total_uses}
                        </div>
                        <div className="text-sm text-gray-500">
                          创建时间: {new Date(token.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`px-2 py-1 rounded text-sm ${
                          token.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {token.status}
                        </div>
                        <Button
                          onClick={() => handleUseToken(token.id)}
                          disabled={token.status !== 'active'}
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