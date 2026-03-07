'use client';

import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { PROVIDER_INFO } from '@/lib/providers';
import { useTranslations } from 'next-intl';
import { Info } from 'lucide-react';

interface ModelSelectorProps {
  provider: string;
  selectedModels: string[];
  enabledModels: string[];  // List of enabled models for this provider
  unavailableModels?: string[];  // List of unavailable models
  modelErrors?: Record<string, string>;  // Model name -> error message
  validating?: boolean;  // Whether models are being validated
  onChange: (models: string[]) => void;
  error?: string;
}

export function ModelSelector({
  provider,
  selectedModels,
  enabledModels,
  unavailableModels = [],
  modelErrors = {},
  validating = false,
  onChange,
  error
}: ModelSelectorProps) {
  const t = useTranslations('shareDialog');
  const tModels = useTranslations('shareDialog.models');
  const tToast = useTranslations('shareDialog.toast');

  // Use enabledModels from props (fetched from API), fallback to hardcoded PROVIDER_INFO
  const supportedModels = enabledModels && enabledModels.length > 0
    ? enabledModels
    : (() => {
        const providerInfo = PROVIDER_INFO[provider as keyof typeof PROVIDER_INFO];
        return providerInfo?.supported_models || [];
      })();

  const handleModelToggle = (model: string) => {
    // 允许用户自由选择任何模型（包括之前标记为不可用的）
    if (selectedModels.includes(model)) {
      onChange(selectedModels.filter(m => m !== model));
    } else {
      onChange([...selectedModels, model]);
    }
  };

  const isModelUnavailable = (model: string) => unavailableModels.includes(model);

  return (
    <div className="space-y-2">
      <Label>{t('selectModels')} <span className="text-red-500">*</span></Label>
      <div className="border rounded-md p-3 space-y-2 max-h-48 overflow-y-auto">
        {validating ? (
          <div className="text-sm text-gray-500 flex items-center gap-2">
            <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-blue-500 rounded-full" />
            {tModels('checking')}
          </div>
        ) : supportedModels.length === 0 ? (
          <div className="text-sm text-gray-500">{t('noModelsAvailable')}</div>
        ) : (
          supportedModels.map((model) => {
            const unavailable = isModelUnavailable(model);
            const errorMsg = modelErrors[model];
            return (
              <div key={model} className="space-y-1">
                <div className={`flex items-center space-x-2 ${unavailable ? 'opacity-70' : ''}`}>
                  <Checkbox
                    id={`model-${model}`}
                    checked={selectedModels.includes(model)}
                    onCheckedChange={() => handleModelToggle(model)}
                  />
                  <label
                    htmlFor={`model-${model}`}
                    className="text-sm font-medium leading-none cursor-pointer"
                  >
                    {model}
                    {unavailable && (
                      <span className="ml-2 text-xs text-orange-600">
                        {tModels('unavailable')}
                      </span>
                    )}
                  </label>
                </div>
                {errorMsg && (
                  <div className="ml-6 flex items-start gap-1 text-xs text-orange-600">
                    <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
      <p className="text-xs text-gray-500">
        {tToast('selectedCount', { count: selectedModels.length })}
      </p>
    </div>
  );
}
