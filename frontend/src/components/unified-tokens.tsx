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
  name: string;
  description?: string;
  token_ids: number[];
  created_at: string;
  total_uses: number;
}

export function UnifiedTokens() {
  const [tokens, setTokens] = useState<UnifiedToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedTokenIds, setSelectedTokenIds] = useState<number[]>([]);
  const [availableTokens, setAvailableTokens] = useState<any[]>([]);
  const { toast } = useToast();

  const loadTokens = async () => {
    try {
      const [unifiedResponse, sharedResponse] = await Promise.all([
        tokenAPI.getMyUnifiedTokens(),
        tokenAPI.getMySharedTokens(),
      ]);

      setTokens(unifiedResponse.data.items);
      setAvailableTokens(sharedResponse.data.items.filter((t: any) => t.status === 'active'));
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
    if (!name || selectedTokenIds.length === 0) {
      toast({
        title: '错误',
        description: '请输入名称并选择至少一个token',
        variant: 'destructive',
      });
      return;
    }

    try {
      await tokenAPI.createUnifiedToken({
        name,
        description,
        token_ids: selectedTokenIds,
      });

      toast({
        title: '成功',
        description: '统一token创建成功',
      });

      setCreateDialogOpen(false);
      setName('');
      setDescription('');
      setSelectedTokenIds([]);
      loadTokens();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.message || '创建失败',
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
        description: error.response?.data?.message || '删除失败',
        variant: 'destructive',
      });
    }
  };

  const toggleTokenSelection = (tokenId: number) => {
    setSelectedTokenIds(prev =>
      prev.includes(tokenId)
        ? prev.filter(id => id !== tokenId)
        : [...prev, tokenId]
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>我的统一Tokens</CardTitle>
          <CardDescription>
            创建和管理您的统一token，将多个共享token组合使用
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
                    选择您分享的tokens来创建一个统一的token组
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
                  <div className="grid grid-cols-4 items-start gap-4">
                    <Label className="text-right pt-2">
                      选择Tokens
                    </Label>
                    <div className="col-span-3 space-y-2">
                      {availableTokens.map((token) => (
                        <div key={token.id} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={`token-${token.id}`}
                            checked={selectedTokenIds.includes(token.id)}
                            onChange={() => toggleTokenSelection(token.id)}
                          />
                          <label htmlFor={`token-${token.id}`} className="text-sm">
                            {token.vendor} - {token.metadata ? JSON.parse(token.metadata).source : '未知'}
                          </label>
                        </div>
                      ))}
                    </div>
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
                        <div className="font-medium">{token.name}</div>
                        {token.description && (
                          <div className="text-sm text-gray-500">{token.description}</div>
                        )}
                        <div className="text-sm text-gray-500">
                          包含 {token.token_ids.length} 个tokens
                        </div>
                        <div className="text-sm text-gray-500">
                          使用次数: {token.total_uses}
                        </div>
                        <div className="text-sm text-gray-500">
                          创建时间: {new Date(token.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          编辑
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteUnifiedToken(token.id)}
                        >
                          删除
                        </Button>
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