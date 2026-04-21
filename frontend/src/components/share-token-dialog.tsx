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
import { getProviderLogo, getProviderBrandName } from '@/lib/providers';
import { useAuthStore } from '@/lib/store';
import Image from 'next/image';
import { useTranslations } from 'next-intl';

interface ShareAPIKeyDialogProps {
  onAPIKeyShared: () => void;
  children?: React.ReactNode;
}

interface Provider {
  id: number;
  provider_key: string;
  name: string;
  website: string;
  logo_path?: string;
  is_enabled: boolean;
}

export function ShareAPIKeyDialog({ onAPIKeyShared, children }: ShareAPIKeyDialogProps) {
  const t = useTranslations('shareDialog');
  const tToast = useTranslations('shareDialog.toast');
  const { currentOrganization } = useAuthStore();

  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState('');
  const [apiKey, setAPIKey] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerModels, setProviderModels] = useState<Record<string, string[]>>({});
  const { toast } = useToast();

  // Load enabled providers on mount
  useEffect(() => {
    let isMounted = true;

    const loadProviders = async () => {
      try {
        setLoadingProviders(true);
        const response = await apiKeyAPI.getProviders();
        if (isMounted) {
          setProviders(response.data.items || []);
        }
      } catch (error: any) {
        if (isMounted) {
          console.error('Failed to load providers:', error);
        }
      } finally {
        if (isMounted) {
          setLoadingProviders(false);
        }
      }
    };

    loadProviders();

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
      }, currentOrganization?.id);

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
              <Label htmlFor="provider" required>
                {t('subscriptionPlatform')}
              </Label>
              <Select value={provider} onValueChange={handleProviderChange} disabled={loadingProviders}>
                <SelectTrigger>
                  {provider ? (() => {
                    const selectedProvider = providers.find(p => p.provider_key === provider);
                    return (
                      <div className="flex items-center gap-2">
                        <Image
                          src={selectedProvider?.logo_path || getProviderLogo(provider)}
                          alt={selectedProvider?.name || getProviderBrandName(provider)}
                          width={20}
                          height={20}
                        />
                        <span>{selectedProvider?.name || getProviderBrandName(provider)}</span>
                      </div>
                    );
                  })() : (
                    <SelectValue placeholder={t('selectPlatform')} />
                  )}
                </SelectTrigger>
                <SelectContent>
                  {providers.map((p) => (
                    <SelectItem key={p.provider_key} value={p.provider_key} className="pl-9">
                      <div className="flex items-center gap-2">
                        <Image
                          src={p.logo_path || getProviderLogo(p.provider_key)}
                          alt={p.name}
                          width={20}
                          height={20}
                        />
                        <span>{p.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="token" required>
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
