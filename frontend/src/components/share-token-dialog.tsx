'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { apiKeyAPI } from '@/lib/services';

interface ShareAPIKeyDialogProps {
  onAPIKeyShared: () => void;
  children?: React.ReactNode;
}

export function ShareAPIKeyDialog({ onAPIKeyShared, children }: ShareAPIKeyDialogProps) {
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState('');
  const [apiKey, setAPIKey] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!provider || !apiKey) {
      toast({
        title: '错误',
        description: '请选择供应商并输入API Key',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      await apiKeyAPI.shareAPIKey({
        provider,
        api_key: apiKey,
        api_key_metadata: JSON.stringify({ source: 'user_input' }),
      });

      toast({
        title: '成功',
        description: '订阅绑定成功',
      });

      setOpen(false);
      setProvider('');
      setAPIKey('');
      onAPIKeyShared();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.message || '绑定失败，请重试',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || <Button>绑定新订阅</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>绑定订阅</DialogTitle>
          <DialogDescription>
            将订阅平台的 APIKey 绑定到平台，平台用户共享使用您的订阅，但不会直接获取 APIKey 信息
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="provider" className="text-right">
                订阅平台
              </Label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="选择平台" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bigmodel">bigmodel</SelectItem>
                  <SelectItem value="z.ai">z.ai</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="token" className="text-right">
                API Key
              </Label>
              <Input
                id="token"
                type="password"
                placeholder="输入您的 API Key"
                value={apiKey}
                onChange={(e) => setAPIKey(e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={loading}>
              {loading ? '绑定中...' : '绑定'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}