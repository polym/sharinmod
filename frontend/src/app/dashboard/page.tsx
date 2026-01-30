'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuthStore } from '@/lib/store';
import { apiKeyAPI } from '@/lib/services';
import { ShareAPIKeyDialog } from '@/components/share-token-dialog';
import { APIKeyDiscovery } from '@/components/token-discovery';
import { UnifiedAPIKeys } from '@/components/unified-tokens';
import { APIKeyUsage } from '@/components/token-usage';
import { ProfileSettings } from '@/components/profile-settings';

interface SharedAPIKey {
  id: number;
  provider: string;
  status: string;
  created_at: string;
  total_uses: number;
  api_key_metadata?: string;
}

export default function DashboardPage() {
  const [sharedAPIKeys, setSharedAPIKeys] = useState<SharedAPIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  // Wait for Zustand hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    loadSharedAPIKeys();
  }, [isAuthenticated, router, isHydrated]);

  const loadSharedAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMySharedAPIKeys();
      setSharedAPIKeys(response.data.items);
    } catch (error) {
      console.error('Failed to load shared API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDisableAPIKey = async (apiKeyId: number) => {
    try {
      await apiKeyAPI.disableSharedAPIKey(apiKeyId);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to disable API key:', error);
      alert('停用失败，请重试');
    }
  };

  const handleEnableAPIKey = async (apiKeyId: number) => {
    try {
      await apiKeyAPI.enableSharedAPIKey(apiKeyId);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to enable API key:', error);
      alert('启用失败，请重试');
    }
  };

  const handleDeleteAPIKey = async (apiKeyId: number) => {
    if (!confirm('确定要删除这个API Key吗？此操作不可撤销。')) {
      return;
    }
    try {
      await apiKeyAPI.deleteSharedAPIKey(apiKeyId);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to delete API key:', error);
      alert('删除失败，请重试');
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
              <TabsTrigger value="discover">发现API Key</TabsTrigger>
              <TabsTrigger value="share">分享API Key</TabsTrigger>
              <TabsTrigger value="unified">我的API Key</TabsTrigger>
              <TabsTrigger value="usage">使用历史</TabsTrigger>
              <TabsTrigger value="profile">个人资料</TabsTrigger>
            </TabsList>

            <TabsContent value="discover">
              <APIKeyDiscovery />
            </TabsContent>

            <TabsContent value="share">
              <Card>
                <CardHeader>
                  <CardTitle>分享您的API Key</CardTitle>
                  <CardDescription>
                    将您的bigmodel或z.ai API Key分享给社区，其他用户可以使用您的API Key进行API调用
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys} />
                </CardContent>
              </Card>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>我分享的API Keys</CardTitle>
                  <CardDescription>
                    您当前分享的API Keys状态
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div>加载中...</div>
                  ) : sharedAPIKeys.length === 0 ? (
                    <div className="text-gray-500">您还没有分享任何API Key</div>
                  ) : (
                    <div className="space-y-4">
                      {sharedAPIKeys.map((apiKey) => (
                        <div key={apiKey.id} className="flex items-center justify-between p-4 border rounded">
                          <div>
                            <div className="font-medium">{apiKey.provider}</div>
                            <div className="text-sm text-gray-500">
                              创建时间: {new Date(apiKey.created_at).toLocaleDateString()}
                            </div>
                            <div className="text-sm text-gray-500">
                              使用次数: {apiKey.total_uses}
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className={`px-2 py-1 rounded text-sm ${
                              apiKey.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {apiKey.status}
                            </div>
                            <div className="flex gap-2">
                              {apiKey.status === 'active' ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleDisableAPIKey(apiKey.id)}
                                >
                                  停用
                                </Button>
                              ) : apiKey.status === 'inactive' ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleEnableAPIKey(apiKey.id)}
                                >
                                  启用
                                </Button>
                              ) : null}
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDeleteAPIKey(apiKey.id)}
                              >
                                删除
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="unified">
              <UnifiedAPIKeys />
            </TabsContent>

            <TabsContent value="usage">
              <APIKeyUsage />
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