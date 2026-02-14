'use client';

import { useState, useEffect } from 'react';
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

export function EditSubscriptionDialog({ apiKey, onUpdated, open, onOpenChange }: EditSubscriptionDialogProps) {
  const t = useTranslations('editSubscriptionDialog');
  const tToast = useTranslations('editSubscriptionDialog.toast');

  const [newApiKey, setNewApiKey] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState('');
  const [loading, setLoading] = useState(false);
  const [providerModels, setProviderModels] = useState<string[]>([]);
  const { toast } = useToast();

  // Load provider models when dialog opens
  useEffect(() => {
    if (open) {
      setSelectedModels(apiKey.supported_models || []);
      setModelError('');
      setNewApiKey('');

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
            </div>
            <ModelSelector
              provider={apiKey.provider}
              selectedModels={selectedModels}
              onChange={setSelectedModels}
              error={modelError}
              enabledModels={providerModels}
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={loading}>
              {loading ? t('saving') : t('save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
