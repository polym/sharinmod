'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/components/ui/toast';
import { Power, PowerOff, RotateCcw, Trash2 } from 'lucide-react';
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
  const [loadingKeys, setLoadingKeys] = useState<Set<number>>(new Set());
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
        description: 'API Key 创建成功',
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
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.blockUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: 'API Key 已停用',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '停用失败',
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleUnblockUnifiedAPIKey = async (id: number) => {
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.unblockUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: 'API Key 已启用',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '启用失败',
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleDeleteUnifiedAPIKey = async (id: number) => {
    if (!confirm('确认删除此 API Key？此操作不可撤销。')) return;
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.deleteUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: 'API Key 删除成功',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '删除失败',
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleRegenerateAPIKey = async (id: number) => {
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.regenerateUnifiedAPIKey(id);
      toast({
        title: '成功',
        description: 'API Key 已重新生成',
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '重新生成失败',
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-1.5">
              <h3 className="text-xl font-semibold leading-none tracking-tight">我的 API Key</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">创建和管理您的 API Key，使用 API Key 调用大模型</p>
            </div>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>创建 API Key</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>创建 API Key</DialogTitle>
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
                      placeholder="API Key 名称"
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
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              您还没有 API Key
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>API Key</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((apiKey) => (
                  <TableRow key={apiKey.id}>
                    <TableCell>{apiKey.api_key_name || '未命名'}</TableCell>
                    <TableCell>
                      {apiKey.litellm_key ? (
                        <span className="font-mono bg-gray-100 p-1 rounded text-sm">
                          {apiKey.litellm_key.length > 8
                            ? `${apiKey.litellm_key.substring(0, 4)}***${apiKey.litellm_key.substring(apiKey.litellm_key.length - 4)}`
                            : apiKey.litellm_key}
                        </span>
                      ) : (
                        <span className="text-gray-500">无</span>
                      )}
                    </TableCell>
                    <TableCell>{apiKey.status === 'active' ? '活跃' : '已停用'}</TableCell>
                    <TableCell>{new Date(apiKey.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {apiKey.status === 'active' && (
                          <>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleRegenerateAPIKey(apiKey.id)}
                              aria-label="重新生成 API Key"
                              disabled={loadingKeys.has(apiKey.id)}
                            >
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleBlockUnifiedAPIKey(apiKey.id)}
                              aria-label="停用 API Key"
                              disabled={loadingKeys.has(apiKey.id)}
                            >
                              <PowerOff className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                        {apiKey.status === 'revoked' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUnblockUnifiedAPIKey(apiKey.id)}
                              aria-label="启用 API Key"
                              disabled={loadingKeys.has(apiKey.id)}
                            >
                              <Power className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteUnifiedAPIKey(apiKey.id)}
                              aria-label="删除 API Key"
                              disabled={loadingKeys.has(apiKey.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}