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
import { PROVIDER_LIST, getProviderLogo, getProviderBrandName } from '@/lib/providers';
import Image from 'next/image';
import { useTranslations } from 'next-intl';

interface ShareAPIKeyDialogProps {
  onAPIKeyShared: () => void;
  children?: React.ReactNode;
}

export function ShareAPIKeyDialog({ onAPIKeyShared, children }: ShareAPIKeyDialogProps) {
  const t = useTranslations('shareDialog');
  const tToast = useTranslations('shareDialog.toast');

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
        title: tToast('error'),
        description: tToast('selectPlatformAndKey'),
        variant: 'destructive',
      });
      return;
    }

    if (selectedModels.length === 0) {
      setModelError(tToast('selectOneModel'));
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
        title: tToast('success'),
        description: tToast('bindSuccess'),
      });

      setOpen(false);
      setProvider('');
      setAPIKey('');
      setSelectedModels([]);
      setModelError('');
      onAPIKeyShared();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.message || tToast('bindFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || <Button variant="ghost" className="bg-brand-100 hover:bg-brand-400 text-brand-500 border border-brand-500">{t('bind')}</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('title')}</DialogTitle>
          <DialogDescription>
            {t('description')}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="provider">
                {t('subscriptionPlatform')}
              </Label>
              <Select value={provider} onValueChange={handleProviderChange}>
                <SelectTrigger>
                  {provider ? (
                    <div className="flex items-center gap-2">
                      <Image src={getProviderLogo(provider)} alt={getProviderBrandName(provider)} width={20} height={20} />
                      <span>{getProviderBrandName(provider)}</span>
                    </div>
                  ) : (
                    <SelectValue placeholder={t('selectPlatform')} />
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
                {t('apiKey')}
              </Label>
              <Input
                id="token"
                type="password"
                placeholder={t('apiKeyPlaceholder')}
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
              {loading ? t('binding') : t('bind')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
