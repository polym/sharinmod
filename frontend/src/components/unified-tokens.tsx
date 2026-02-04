'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/components/ui/toast';
import { Copy, Edit, Trash2, Check } from 'lucide-react';
import { apiKeyAPI } from '@/lib/services';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';

interface UnifiedAPIKey {
  id: number;
  api_key_name: string;
  description?: string; // Optional: User-provided description, may be null for older keys
  api_key: string;
  status: string;
  litellm_key?: string;
  created_at: string;
  revoked_at?: string;
  last_used_at?: string;
}

export function UnifiedAPIKeys() {
  const [apiKeys, setAPIKeys] = useState<UnifiedAPIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [editingKey, setEditingKey] = useState<UnifiedAPIKey | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editEnabled, setEditEnabled] = useState(true);
  const [loadingKeys, setLoadingKeys] = useState<Set<number>>(new Set());
  const [copiedKeyId, setCopiedKeyId] = useState<number | null>(null);
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

  const handleEditAPIKey = (apiKey: UnifiedAPIKey) => {
    setEditingKey(apiKey);
    setEditName(apiKey.api_key_name || '');
    setEditDescription(apiKey.description || '');
    setEditEnabled(apiKey.status === 'active');
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingKey) return;
    
    if (!editName) {
      toast({
        title: '错误',
        description: '请输入名称',
        variant: 'destructive',
      });
      return;
    }

    // Confirm if disabling an active key
    if (editingKey.status === 'active' && !editEnabled) {
      if (!confirm('确认要停用此 API Key？停用后将无法使用该密钥调用 API。')) {
        return;
      }
    }

    try {
      await apiKeyAPI.updateUnifiedAPIKey(editingKey.id, {
        api_key_name: editName,
        description: editDescription,
        status: editEnabled ? 'active' : 'revoked',
      });

      toast({
        title: '成功',
        description: 'API Key 更新成功',
      });

      setEditDialogOpen(false);
      setEditingKey(null);
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '更新失败',
        variant: 'destructive',
      });
    }
  };

  const handleCopyAPIKey = (key: string, id: number) => {
    // Try modern clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(key).then(() => {
        setCopiedKeyId(id);
        setTimeout(() => setCopiedKeyId(null), 1500);
      }).catch(() => {
        fallbackCopy(key, id);
      });
    } else {
      fallbackCopy(key, id);
    }
  };

  const fallbackCopy = (text: string, id: number) => {
    // Fallback for older browsers or non-HTTPS contexts
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      setCopiedKeyId(id);
      setTimeout(() => setCopiedKeyId(null), 1500);
    } catch (err) {
      toast({
        title: '错误',
        description: '复制失败，请手动复制',
        variant: 'destructive',
      });
    }
    document.body.removeChild(textArea);
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
      // First revoke if active
      const apiKey = apiKeys.find(k => k.id === id);
      if (apiKey?.status === 'active') {
        await apiKeyAPI.blockUnifiedAPIKey(id);
      }
      // Then delete
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
                <Button variant="ghost" className="bg-brand-100 hover:bg-brand-400 text-brand-500 border border-brand-500">创建 API Key</Button>
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
                    <Textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="col-span-3"
                      placeholder="可选描述"
                      rows={3}
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
                  <TableHead>最近使用时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((apiKey) => (
                  <TableRow key={apiKey.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{apiKey.api_key_name || '未命名'}</span>
                        {apiKey.description && (
                          <span 
                            className="text-xs text-gray-400 line-clamp-2 break-words" 
                            title={apiKey.description}
                          >
                            {apiKey.description}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {apiKey.litellm_key ? (
                          <>
                            <span className="font-mono bg-gray-100 p-1 rounded text-sm">
                              {apiKey.litellm_key.length > 10
                                ? `${apiKey.litellm_key.substring(0, 6)}***${apiKey.litellm_key.substring(apiKey.litellm_key.length - 4)}`
                                : apiKey.litellm_key}
                            </span>
                            <div className="flex items-center w-[92px]">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleCopyAPIKey(apiKey.litellm_key!, apiKey.id)}
                                aria-label="复制 API Key"
                                className="h-6 w-6 p-0"
                              >
                                {copiedKeyId === apiKey.id ? (
                                  <Check className="h-3 w-3 text-purple-600" />
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                              </Button>
                              {copiedKeyId === apiKey.id && (
                                <span className="text-xs text-purple-600 ml-1 inline-block w-16">
                                  已复制！
                                </span>
                              )}
                            </div>
                          </>
                        ) : (
                          <span className="text-gray-500">无</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                        apiKey.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {apiKey.status === 'active' ? '活跃' : '已停用'}
                      </span>
                    </TableCell>
                    <TableCell>
                      {new Date(apiKey.created_at).toLocaleString('zh-CN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false
                      })}
                    </TableCell>
                    <TableCell>
                      {apiKey.last_used_at
                        ? new Date(apiKey.last_used_at).toLocaleString('zh-CN', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false
                          })
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleEditAPIKey(apiKey)}
                          aria-label="编辑 API Key"
                          disabled={loadingKeys.has(apiKey.id)}
                        >
                          <Edit className="h-4 w-4" />
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

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>编辑 API Key</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-name" className="text-right">
                名称
              </Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="col-span-3"
                placeholder="API Key 名称"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-description" className="text-right">
                描述
              </Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="col-span-3"
                placeholder="可选描述"
                rows={3}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-enabled" className="text-right">
                启用状态
              </Label>
              <div className="col-span-3 flex items-center gap-2">
                <Switch
                  id="edit-enabled"
                  checked={editEnabled}
                  onCheckedChange={setEditEnabled}
                />
                <span className="text-sm text-gray-600">
                  {editEnabled ? '已启用' : '已停用'}
                </span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSaveEdit}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}