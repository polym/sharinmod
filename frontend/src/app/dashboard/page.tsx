'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuthStore } from '@/lib/store';
import { tokenAPI } from '@/lib/services';
import { ShareTokenDialog } from '@/components/share-token-dialog';
import { TokenDiscovery } from '@/components/token-discovery';
import { UnifiedTokens } from '@/components/unified-tokens';
import { TokenUsage } from '@/components/token-usage';
import { ProfileSettings } from '@/components/profile-settings';

interface SharedToken {
  id: number;
  vendor: string;
  status: string;
  created_at: string;
  total_uses: number;
  metadata?: string;
}

export default function DashboardPage() {
  const [sharedTokens, setSharedTokens] = useState<SharedToken[]>([]);
  const [loading, setLoading] = useState(true);
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    loadSharedTokens();
  }, [isAuthenticated, router]);

  const loadSharedTokens = async () => {
    try {
      const response = await tokenAPI.getMySharedTokens();
      setSharedTokens(response.data.items);
    } catch (error) {
      console.error('Failed to load shared tokens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">SharinMod</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">欢迎, {user?.email}</span>
              <Button variant="outline" onClick={handleLogout}>
                登出
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <Tabs defaultValue="discover" className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="discover">发现Token</TabsTrigger>
              <TabsTrigger value="share">分享Token</TabsTrigger>
              <TabsTrigger value="unified">我的Token</TabsTrigger>
              <TabsTrigger value="usage">使用历史</TabsTrigger>
              <TabsTrigger value="profile">个人资料</TabsTrigger>
            </TabsList>

            <TabsContent value="discover">
              <TokenDiscovery />
            </TabsContent>

            <TabsContent value="share">
              <Card>
                <CardHeader>
                  <CardTitle>分享您的API Token</CardTitle>
                  <CardDescription>
                    将您的bigmodel或z.ai API token分享给社区，其他用户可以使用您的token进行API调用
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ShareTokenDialog onTokenShared={loadSharedTokens} />
                </CardContent>
              </Card>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>我分享的Tokens</CardTitle>
                  <CardDescription>
                    您当前分享的API tokens状态
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div>加载中...</div>
                  ) : sharedTokens.length === 0 ? (
                    <div className="text-gray-500">您还没有分享任何token</div>
                  ) : (
                    <div className="space-y-4">
                      {sharedTokens.map((token) => (
                        <div key={token.id} className="flex items-center justify-between p-4 border rounded">
                          <div>
                            <div className="font-medium">{token.vendor}</div>
                            <div className="text-sm text-gray-500">
                              创建时间: {new Date(token.created_at).toLocaleDateString()}
                            </div>
                            <div className="text-sm text-gray-500">
                              使用次数: {token.total_uses}
                            </div>
                          </div>
                          <div className={`px-2 py-1 rounded text-sm ${
                            token.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {token.status}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="unified">
              <UnifiedTokens />
            </TabsContent>

            <TabsContent value="usage">
              <TokenUsage />
            </TabsContent>

            <TabsContent value="profile">
              <ProfileSettings />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}