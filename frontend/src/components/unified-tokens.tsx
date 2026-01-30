'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { apiKeyAPI } from '@/lib/services';

interface UnifiedAPIKey {
  id: number;
  api_key_name: string;
  api_key: string;
  status: string;
  litellm_key?: string;
  created_at: string;
  revoked_at?: string;
}

export function UnifiedAPIKeys() {
  const [apiKeys, setAPIKeys] = useState<UnifiedAPIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const { toast } = useToast();

  const loadAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMyUnifiedAPIKeys();
      setAPIKeys(response.data.items);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAPIKeys();
  }, []);

  const handleCreateUnifiedAPIKey = async () => {
    if (!name) {
      toast({
        title: '错误',
        description: '请输入名称',
        variant: 'destructive',
      });
      return;
    }

    try {
      await apiKeyAPI.createUnifiedAPIKey({
        api_key_name: name,
        description,
        api_key_ids: [],
      });

      toast({
        title: '成功',
        description: '统一API Key创建成功',
      });

      setCreateDialogOpen(false);
      setName('');
      setDescription('');
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '创建失败',
        variant: 'destructive',
      });
    }
  };

  const handleBlockUnifiedAPIKey = async (id: number) => {
    try {
      await apiKeyAPI.blockUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: '统一API Key已停用',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '停用失败',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUnifiedAPIKey = async (id: number) => {
    try {
      await apiKeyAPI.deleteUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: '统一API Key删除成功',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '删除失败',
        variant: 'destructive',
      });
    }
  };

  const handleRegenerateAPIKey = async (id: number) => {
    try {
      await apiKeyAPI.regenerateUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: 'API Key已重新生成',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '重新生成失败',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>我的统一API Keys</CardTitle>
          <CardDescription>
            创建和管理您的统一 API Key
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center mb-6">
            <div></div>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>创建统一API Key</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>创建统一API Key</DialogTitle>
                  <DialogDescription>
                    创建一个新的统一 API Key
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                      名称
                    </Label>
                    <Input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="col-span-3"
                      placeholder="统一API Key名称"
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="description" className="text-right">
                      描述
                    </Label>
                    <Input
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="col-span-3"
                      placeholder="可选描述"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={handleCreateUnifiedAPIKey}>
                    创建
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              您还没有创建任何统一API Key
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((apiKey) => (
                <Card key={apiKey.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">{apiKey.api_key_name || '未命名'}</div>
                        <div className="text-sm text-gray-500">
                          状态: {apiKey.status === 'active' ? '活跃' : '已停用'}
                        </div>
                        {apiKey.litellm_key && apiKey.litellm_key.length > 16 && (
                          <div className="text-sm font-mono bg-gray-100 p-2 rounded">
                            {apiKey.litellm_key.substring(0, 8)}***{apiKey.litellm_key.substring(apiKey.litellm_key.length - 8)}
                          </div>
                        )}
                        {apiKey.litellm_key && apiKey.litellm_key.length <= 16 && (
                          <div className="text-sm font-mono bg-gray-100 p-2 rounded">
                            {apiKey.litellm_key.substring(0, 4)}***{apiKey.litellm_key.substring(apiKey.litellm_key.length - 4)}
                          </div>
                        )}
                        <div className="text-sm text-gray-500">
                          创建时间: {new Date(apiKey.created_at).toLocaleDateString()}
                        </div>
                        {apiKey.revoked_at && (
                          <div className="text-sm text-gray-500">
                            停用时间: {new Date(apiKey.revoked_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {apiKey.status === 'active' && (
                          <>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleRegenerateAPIKey(apiKey.id)}
                            >
                              重新生成
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleBlockUnifiedAPIKey(apiKey.id)}
                            >
                              停用
                            </Button>
                          </>
                        )}
                        {apiKey.status === 'revoked' && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDeleteUnifiedAPIKey(apiKey.id)}
                          >
                            删除
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}