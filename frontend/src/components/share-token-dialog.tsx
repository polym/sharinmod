'use client';

import { useState, useEffect } from 'react';
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
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [enabledProviders, setEnabledProviders] = useState<Record<string, boolean>>({});
  const [providerModels, setProviderModels] = useState<Record<string, string[]>>({});
  const { toast } = useToast();

  // Load enabled providers on mount
  useEffect(() => {
    let isMounted = true;

    const loadEnabledProviders = async () => {
      try {
        setLoadingProviders(true);
        // Note: adminAPI.getProviders requires admin privileges, so we'll skip this for regular users
        // and rely on the hardcoded provider list with a fallback mechanism
        if (!isMounted) return;

        const enabledMap: Record<string, boolean> = {};
        // For now, enable all providers by default since admin API requires privileges
        PROVIDER_LIST.forEach(p => {
          enabledMap[p.code] = true;
        });
        setEnabledProviders(enabledMap);
      } catch (error: any) {
        if (!isMounted) return;
        console.error('Failed to load enabled providers:', error);
      } finally {
        if (isMounted) {
          setLoadingProviders(false);
        }
      }
    };

    loadEnabledProviders();

    return () => {
      isMounted = false;
    };
  }, []);

  // Reset models when provider changes
  const handleProviderChange = async (value: string) => {
    setProvider(value);
    setSelectedModels([]);
    setModelError('');

    // Load models for this provider
    try {
      const response = await apiKeyAPI.getProviderModels(value);
      setProviderModels(prev => ({ ...prev, [value]: response.data.supported_models || [] }));
    } catch (error) {
      console.error('Failed to load provider models:', error);
      // Fallback to hardcoded models
      setProviderModels(prev => ({ ...prev, [value]: [] }));
    }
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
              <Select value={provider} onValueChange={handleProviderChange} disabled={loadingProviders}>
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
                  {PROVIDER_LIST.filter(p => {
                    // If enabledProviders is empty (API failed), show all providers
                    const isEmpty = Object.keys(enabledProviders).length === 0;
                    return isEmpty || enabledProviders[p.code] ?? false;
                  }).map((p) => (
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
                enabledModels={providerModels[provider] || []}
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
