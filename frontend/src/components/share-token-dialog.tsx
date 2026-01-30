'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { tokenAPI } from '@/lib/services';

interface ShareTokenDialogProps {
  onTokenShared: () => void;
}

export function ShareTokenDialog({ onTokenShared }: ShareTokenDialogProps) {
  const [open, setOpen] = useState(false);
  const [vendor, setVendor] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vendor || !token) {
      toast({
        title: '错误',
        description: '请选择供应商并输入API token',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      await tokenAPI.shareToken({
        vendor,
        token,
        metadata: JSON.stringify({ source: 'user_input' }),
      });

      toast({
        title: '成功',
        description: 'Token分享成功',
      });

      setOpen(false);
      setVendor('');
      setToken('');
      onTokenShared();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.message || '分享失败，请重试',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>分享新Token</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>分享API Token</DialogTitle>
          <DialogDescription>
            将您的API token分享给社区，其他用户可以使用您的token进行API调用
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="vendor" className="text-right">
                供应商
              </Label>
              <Select value={vendor} onValueChange={setVendor}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bigmodel">bigmodel</SelectItem>
                  <SelectItem value="z.ai">z.ai</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="token" className="text-right">
                API Token
              </Label>
              <Input
                id="token"
                type="password"
                placeholder="输入您的API token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={loading}>
              {loading ? '分享中...' : '分享'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}