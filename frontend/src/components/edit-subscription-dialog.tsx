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

interface EditSubscriptionDialogProps {
  apiKey: SharedAPIKey;
  onUpdated: () => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditSubscriptionDialog({ apiKey, onUpdated, open, onOpenChange }: EditSubscriptionDialogProps) {
  const [newApiKey, setNewApiKey] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Pre-fill data when dialog opens
  useEffect(() => {
    if (open) {
      setSelectedModels(apiKey.supported_models || []);
      setModelError('');
      setNewApiKey('');
    }
  }, [open, apiKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedModels.length === 0) {
      setModelError('请至少选择一个模型');
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
        title: '成功',
        description: '订阅修改成功',
      });

      onOpenChange(false);
      setNewApiKey('');
      setSelectedModels([]);
      setModelError('');
      onUpdated();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.message || '修改失败，请重试',
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
          <DialogTitle>修改订阅</DialogTitle>
          <DialogDescription>
            修改 {getProviderBrandName(apiKey.provider)} 订阅的 API Key 和可用模型
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="token">
                API Key
              </Label>
              <Input
                id="token"
                type="password"
                placeholder="留空表示不修改 API Key"
                value={newApiKey}
                onChange={(e) => setNewApiKey(e.target.value)}
              />
            </div>
            <ModelSelector
              provider={apiKey.provider}
              selectedModels={selectedModels}
              onChange={setSelectedModels}
              error={modelError}
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={loading}>
              {loading ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
