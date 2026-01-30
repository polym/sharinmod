'use client';

import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShareAPIKeyDialog } from '@/components/share-token-dialog';
import { apiKeyAPI } from '@/lib/services';
import { SharedAPIKey } from '@/types/apiKey';

export function MySharedPage() {
  const [sharedAPIKeys, setSharedAPIKeys] = useState<SharedAPIKey[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSharedAPIKeys();
  }, []);

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

  return (
    <div className="max-w-7xl mx-auto p-8">
      <Card>
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-1.5">
              <h3 className="text-xl font-semibold leading-none tracking-tight">已分享的 API Keys</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">启用、停用或删除您的共享 API Keys</p>
            </div>
            <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys}>
              <Button className="bg-brand-500 hover:bg-brand-600">
                <Plus className="w-4 h-4 mr-2" />
                分享新 API Key
              </Button>
            </ShareAPIKeyDialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">加载中...</div>
            </div>
          ) : sharedAPIKeys.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-500 mb-4">暂无共享的 API Key</div>
              <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys}>
                <Button variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  分享您的第一个 API Key
                </Button>
              </ShareAPIKeyDialog>
            </div>
          ) : (
            <div className="space-y-4">
              {sharedAPIKeys.map((apiKey) => (
                <div
                  key={apiKey.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-lg gap-4"
                >
                  <div className="space-y-1">
                    <div className="font-medium text-gray-900">{apiKey.provider}</div>
                    <div className="text-sm text-gray-500">
                      创建时间: {new Date(apiKey.created_at).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      使用次数: {apiKey.total_uses}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                        apiKey.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {apiKey.status === 'active' ? '活跃' : '已停用'}
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
    </div>
  );
}
