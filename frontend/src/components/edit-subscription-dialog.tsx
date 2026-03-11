'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { ModelSelector } from '@/components/ModelSelector';
import { apiKeyAPI } from '@/lib/services';
import { getProviderBrandName } from '@/lib/providers';
import { SharedAPIKey } from '@/types/apiKey';
import { useTranslations } from 'next-intl';

interface EditSubscriptionDialogProps {
  apiKey: SharedAPIKey;
  onUpdated: () => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
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

export function EditSubscriptionDialog({ apiKey, onUpdated, open, onOpenChange }: EditSubscriptionDialogProps) {
  const t = useTranslations('editSubscriptionDialog');
  const tToast = useTranslations('editSubscriptionDialog.toast');

  const [newApiKey, setNewApiKey] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState('');
  const [loading, setLoading] = useState(false);
  const [providerModels, setProviderModels] = useState<string[]>([]);
  const [unavailableModels, setUnavailableModels] = useState<string[]>([]);
  const [modelErrors, setModelErrors] = useState<Record<string, string>>({});
  const [validating, setValidating] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const { toast } = useToast();

  // Debounced model validation function
  const validateModels = useCallback(async () => {
    // 只有当用户输入了新的 API Key 时才进行验证
    if (!newApiKey || selectedModels.length === 0) {
      setUnavailableModels([]);
      setAvailableModels([]);
      setModelErrors({});
      setValidating(false);
      return;
    }

    setValidating(true);
    try {
      const response = await apiKeyAPI.validateModels({
        provider: apiKey.provider,
        api_key: newApiKey,
        selected_models: selectedModels,
      });
      setUnavailableModels(response.data.unavailable_models || []);
      setAvailableModels(response.data.available_models || []);
      setModelErrors(response.data.model_errors || {});
    } catch (error) {
      // Ignore validation errors, keep empty lists
      setUnavailableModels([]);
      setAvailableModels([]);
      setModelErrors({});
    } finally {
      setValidating(false);
    }
  }, [apiKey.provider, newApiKey, selectedModels]);

  const debouncedValidate = useDebounce(validateModels, 800);

  // Trigger validation when newApiKey or selectedModels changes
  useEffect(() => {
    debouncedValidate();
  }, [debouncedValidate, newApiKey, selectedModels]);

  // Load provider models when dialog opens
  useEffect(() => {
    if (open) {
      setSelectedModels(apiKey.supported_models || []);
      setModelError('');
      setNewApiKey('');
      setUnavailableModels([]);
      setAvailableModels([]);
      setModelErrors({});

      // Fetch models for this provider
      apiKeyAPI.getProviderModels(apiKey.provider)
        .then(response => {
          setProviderModels(response.data.supported_models || []);
        })
        .catch(error => {
          console.error('Failed to load provider models:', error);
          setProviderModels([]);
        });
    }
  }, [open, apiKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedModels.length === 0) {
      setModelError(tToast('selectOneModel'));
      return;
    }

    setLoading(true);
    setModelError('');
    try {
      await apiKeyAPI.updateSharedAPIKey(apiKey.id, {
        api_key: newApiKey || undefined,
        selected_models: selectedModels,
      });

      toast({
        title: tToast('success'),
        description: tToast('editSuccess'),
      });

      onOpenChange(false);
      setNewApiKey('');
      setSelectedModels([]);
      setModelError('');
      setUnavailableModels([]);
      setModelErrors({});
      onUpdated();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.message || tToast('editFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('title')}</DialogTitle>
          <DialogDescription>
            {t('description', { provider: getProviderBrandName(apiKey.provider) })}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="token">
                {t('apiKey')}
              </Label>
              <Input
                id="token"
                type="password"
                placeholder={t('apiKeyPlaceholder')}
                value={newApiKey}
                onChange={(e) => setNewApiKey(e.target.value)}
              />
              {newApiKey && validating && (
                <div className="text-xs text-gray-500 flex items-center gap-2">
                  <div className="animate-spin h-3 w-3 border-2 border-gray-300 border-t-blue-500 rounded-full" />
                  {tToast('checking')}
                </div>
              )}
            </div>
            <ModelSelector
              provider={apiKey.provider}
              selectedModels={selectedModels}
              onChange={setSelectedModels}
              error={modelError}
              enabledModels={providerModels}
              unavailableModels={unavailableModels}
              modelErrors={modelErrors}
              validating={validating}
            />
          </div>
          <DialogFooter>
            <Button
              type="submit"
              disabled={loading || validating || (newApiKey && selectedModels.length > 0 && availableModels.length === 0)}
            >
              {loading ? t('saving') : t('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
