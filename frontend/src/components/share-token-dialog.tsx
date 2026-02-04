'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { ModelSelector } from '@/components/ModelSelector';
import { apiKeyAPI } from '@/lib/services';
import { PROVIDER_LIST, getProviderLogo, getProviderBrandName, PROVIDER_INFO } from '@/lib/providers';
import Image from 'next/image';

interface ShareAPIKeyDialogProps {
  onAPIKeyShared: () => void;
  children?: React.ReactNode;
}

export function ShareAPIKeyDialog({ onAPIKeyShared, children }: ShareAPIKeyDialogProps) {
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState('');
  const [apiKey, setAPIKey] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Reset models when provider changes
  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    setSelectedModels([]);
    setModelError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!provider || !apiKey) {
      toast({
        title: '错误',
        description: '请选择平台并输入 API Key',
        variant: 'destructive',
      });
      return;
    }

    if (selectedModels.length === 0) {
      setModelError('请至少选择一个模型');
      return;
    }

    setLoading(true);
    setModelError('');
    try {
      await apiKeyAPI.shareAPIKey({
        provider,
        api_key: apiKey,
        api_key_metadata: JSON.stringify({ source: 'user_input' }),
        selected_models: selectedModels,
      });

      toast({
        title: '成功',
        description: '订阅绑定成功',
      });

      setOpen(false);
      setProvider('');
      setAPIKey('');
      setSelectedModels([]);
      setModelError('');
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
        {children || <Button variant="ghost" className="bg-brand-100 hover:bg-brand-400 text-brand-500 border border-brand-500">绑定新订阅</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>绑定订阅</DialogTitle>
          <DialogDescription>
            将订阅平台的 APIKey 绑定到平台，平台用户共享使用您的订阅，但不会直接获取 APIKey 信息
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="provider">
                订阅平台
              </Label>
              <Select value={provider} onValueChange={handleProviderChange}>
                <SelectTrigger>
                  {provider ? (
                    <div className="flex items-center gap-2">
                      <Image src={getProviderLogo(provider)} alt={getProviderBrandName(provider)} width={20} height={20} />
                      <span>{getProviderBrandName(provider)}</span>
                    </div>
                  ) : (
                    <SelectValue placeholder="选择平台" />
                  )}
                </SelectTrigger>
                <SelectContent>
                  {PROVIDER_LIST.map((p) => (
                    <SelectItem key={p.code} value={p.code} className="pl-2">
                      <div className="flex items-center gap-2">
                        <Image src={p.logoPath} alt={p.brandName} width={20} height={20} />
                        <span>{p.brandName}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="token">
                API Key
              </Label>
              <Input
                id="token"
                type="password"
                placeholder="输入您的 API Key"
                value={apiKey}
                onChange={(e) => setAPIKey(e.target.value)}
              />
            </div>
            {provider && (
              <ModelSelector
                provider={provider}
                selectedModels={selectedModels}
                onChange={setSelectedModels}
                error={modelError}
              />
            )}
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
