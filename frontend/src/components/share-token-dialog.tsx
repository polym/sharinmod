'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { ModelSelector } from '@/components/ModelSelector';
import { apiKeyAPI } from '@/lib/services';
import { getProviderLogo, getProviderBrandName } from '@/lib/providers';
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

// Debounce hook
function useDebounce<T extends (...args: any[]) => any>(callback: T, delay: number): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  const debouncedCallback = useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  return debouncedCallback as T;
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
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerModels, setProviderModels] = useState<Record<string, string[]>>({});
  const [unavailableModels, setUnavailableModels] = useState<string[]>([]);
  const [modelErrors, setModelErrors] = useState<Record<string, string>>({});
  const [validating, setValidating] = useState(false);
  const { toast } = useToast();

  // Debounced model validation function
  const validateModels = useCallback(async () => {
    if (!provider || !apiKey || selectedModels.length === 0) {
      setUnavailableModels([]);
      setModelErrors({});
      setValidating(false);
      return;
    }

    setValidating(true);
    try {
      const response = await apiKeyAPI.validateModels({
        provider,
        api_key: apiKey,
        selected_models: selectedModels,
      });
      setUnavailableModels(response.data.unavailable_models || []);
      setModelErrors(response.data.model_errors || {});
    } catch (error) {
      // Ignore validation errors, keep empty lists
      setUnavailableModels([]);
      setModelErrors({});
    } finally {
      setValidating(false);
    }
  }, [provider, apiKey, selectedModels]);

  const debouncedValidate = useDebounce(validateModels, 800);

  // Trigger validation when apiKey, selectedModels, or provider changes
  useEffect(() => {
    debouncedValidate();
  }, [debouncedValidate, apiKey, selectedModels, provider]);

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
    setUnavailableModels([]);  // Reset unavailable models
    setModelErrors({});  // Reset model errors

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

    // 不再阻止用户提交包含不可用模型的请求
    // 用户可以看到错误信息，但仍可尝试提交
    // 如果后端验证失败，会返回错误

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
      setUnavailableModels([]);
      setModelErrors({});
      onAPIKeyShared();
    } catch (error: any) {
      // Handle backend validation error for unavailable models
      if (error.response?.data?.code === 'models_unavailable') {
        const unavailableList = error.response.data.unavailable_models || [];
        const errors = error.response.data.model_errors || {};
        setUnavailableModels(unavailableList);
        setModelErrors(errors);
        toast({
          title: tToast('error'),
          description: tToast('modelsUnavailable', { models: unavailableList.join(', ') }),
          variant: 'destructive',
        });
      } else {
        toast({
          title: tToast('error'),
          description: error.response?.data?.message || tToast('bindFailed'),
          variant: 'destructive',
        });
      }
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
                unavailableModels={unavailableModels}
                modelErrors={modelErrors}
                validating={validating}
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
