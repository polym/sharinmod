'use client';

import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { PROVIDER_INFO } from '@/lib/providers';
import { useTranslations } from 'next-intl';

interface ModelSelectorProps {
  provider: string;
  selectedModels: string[];
  enabledModels: string[];  // List of enabled models for this provider
  onChange: (models: string[]) => void;
  error?: string;
}

export function ModelSelector({ provider, selectedModels, enabledModels, onChange, error }: ModelSelectorProps) {
  const t = useTranslations('shareDialog');

  // Use enabledModels from props (fetched from API), fallback to hardcoded PROVIDER_INFO
  const supportedModels = enabledModels && enabledModels.length > 0
    ? enabledModels
    : (() => {
        const providerInfo = PROVIDER_INFO[provider as keyof typeof PROVIDER_INFO];
        return providerInfo?.supported_models || [];
      })();

  const handleModelToggle = (model: string) => {
    if (selectedModels.includes(model)) {
      onChange(selectedModels.filter(m => m !== model));
    } else {
      onChange([...selectedModels, model]);
    }
  };

  return (
    <div className="space-y-2">
      <Label>{t('selectModels')} <span className="text-red-500">*</span></Label>
      <div className="border rounded-md p-3 space-y-2 max-h-48 overflow-y-auto">
        {supportedModels.length === 0 ? (
          <div className="text-sm text-gray-500">{t('noModelsAvailable')}</div>
        ) : (
          supportedModels.map((model) => (
            <div key={model} className="flex items-center space-x-2">
              <Checkbox
                id={`model-${model}`}
                checked={selectedModels.includes(model)}
                onCheckedChange={() => handleModelToggle(model)}
              />
              <label
                htmlFor={`model-${model}`}
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
              >
                {model}
              </label>
            </div>
          ))
        )}
      </div>
      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
      <p className="text-xs text-gray-500">
        {t('toast.selectedCount', { count: selectedModels.length })}
      </p>
    </div>
  );
}
