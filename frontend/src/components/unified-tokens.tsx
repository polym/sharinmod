'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { tokenAPI } from '@/lib/services';

interface UnifiedToken {
  id: number;
  token_name: string;
  token: string;
  status: string;
  litellm_key?: string;
  created_at: string;
  revoked_at?: string;
}

export function UnifiedTokens() {
  const [tokens, setTokens] = useState<UnifiedToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const { toast } = useToast();

  const loadTokens = async () => {
    try {
      const response = await tokenAPI.getMyUnifiedTokens();
      setTokens(response.data.items);
    } catch (error) {
      console.error('Failed to load tokens:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTokens();
  }, []);

  const handleCreateUnifiedToken = async () => {
    if (!name) {
      toast({
        title: '错误',
        description: '请输入名称',
        variant: 'destructive',
      });
      return;
    }

    try {
      await tokenAPI.createUnifiedToken({
        token_name: name,
        description,
        token_ids: [],
      });

      toast({
        title: '成功',
        description: '统一token创建成功',
      });

      setCreateDialogOpen(false);
      setName('');
      setDescription('');
      loadTokens();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '创建失败',
        variant: 'destructive',
      });
    }
  };

  const handleBlockUnifiedToken = async (id: number) => {
    try {
      await tokenAPI.blockUnifiedToken(id);
      toast({
        title: '成功',
        description: '统一token已停用',
      });
      loadTokens();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '停用失败',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUnifiedToken = async (id: number) => {
    try {
      await tokenAPI.deleteUnifiedToken(id);
      toast({
        title: '成功',
        description: '统一token删除成功',
      });
      loadTokens();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '删除失败',
        variant: 'destructive',
      });
    }
  };

  const handleRegenerateToken = async (id: number) => {
    try {
      await tokenAPI.regenerateUnifiedToken(id);
      toast({
        title: '成功',
        description: 'API Key已重新生成',
      });
      loadTokens();
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
          <CardTitle>我的统一Tokens</CardTitle>
          <CardDescription>
            创建和管理您的统一 API Token
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center mb-6">
            <div></div>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>创建统一Token</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>创建统一Token</DialogTitle>
                  <DialogDescription>
                    创建一个新的统一 API Token
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
                      placeholder="统一token名称"
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
                  <Button onClick={handleCreateUnifiedToken}>
                    创建
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : tokens.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              您还没有创建任何统一token
            </div>
          ) : (
            <div className="space-y-4">
              {tokens.map((token) => (
                <Card key={token.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">{token.token_name || '未命名'}</div>
                        <div className="text-sm text-gray-500">
                          状态: {token.status === 'active' ? '活跃' : '已停用'}
                        </div>
                        {token.litellm_key && token.litellm_key.length > 16 && (
                          <div className="text-sm font-mono bg-gray-100 p-2 rounded">
                            {token.litellm_key.substring(0, 8)}***{token.litellm_key.substring(token.litellm_key.length - 8)}
                          </div>
                        )}
                        {token.litellm_key && token.litellm_key.length <= 16 && (
                          <div className="text-sm font-mono bg-gray-100 p-2 rounded">
                            {token.litellm_key.substring(0, 4)}***{token.litellm_key.substring(token.litellm_key.length - 4)}
                          </div>
                        )}
                        <div className="text-sm text-gray-500">
                          创建时间: {new Date(token.created_at).toLocaleDateString()}
                        </div>
                        {token.revoked_at && (
                          <div className="text-sm text-gray-500">
                            停用时间: {new Date(token.revoked_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {token.status === 'active' && (
                          <>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleRegenerateToken(token.id)}
                            >
                              重新生成
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleBlockUnifiedToken(token.id)}
                            >
                              停用
                            </Button>
                          </>
                        )}
                        {token.status === 'revoked' && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDeleteUnifiedToken(token.id)}
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