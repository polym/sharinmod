'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Copy, Check, Type, Image as ImageIcon, Video, Mic, Code2, File } from 'lucide-react';
import Image from 'next/image';
import { getModelLogo } from '@/lib/providers';
import type { SharedBy } from '@/types/model';
import { useTranslations } from 'next-intl';

const COPY_FEEDBACK_DURATION = 1500; // ms

interface ModelCardProps {
  model: {
    display_name: string;
    model_name: string;
    description: string;
    input_types: string[];
    output_types: string[];
    context_length: string;
    max_output_length: string;
    available_subscriptions: number;
    shared_by: SharedBy[];
    provider: string;
    used_tokens?: number;
    coding_score?: number | null;
    providers?: Array<{ code: string; name: string; logo_path: string }>;
    subscription_platform_count?: number;
    model_logo?: string;
    model_logo_url?: string;
  };
  onQuickCall?: (modelName: string) => void;
}

// 输入/输出类型图标映射
const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Text': Type,
  'Image': ImageIcon,
  'Video': Video,
  'Audio': Mic,
  'File': File,
};

// 所有支持的类型
const ALL_TYPES = ['Text', 'Image', 'Video', 'Audio', 'File'] as const;

// 提供商 Logo Tooltip 组件
function ProviderLogoTooltip({ provider, children, providerName }: { provider: { code: string; logo_path: string }; children: React.ReactNode; providerName: string }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className="clay-tooltip absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 z-50 pointer-events-none whitespace-nowrap">
          {providerName}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-indigo-900/90" />
        </div>
      )}
    </div>
  );
}

// 分享者头像 Tooltip 组件
function SharerAvatarTooltip({ name, children }: { name: string; children: React.ReactNode }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className="clay-tooltip absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 z-50 pointer-events-none whitespace-nowrap">
          {name}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-indigo-900/90" />
        </div>
      )}
    </div>
  );
}

// 输入/输出类型中文标签映射
const TYPE_LABELS: Record<string, string> = {
  'Text': '文本',
  'Image': '图片',
  'Video': '视频',
  'Audio': '音频',
  'File': '文件',
};

export function ModelCard({ model, onQuickCall }: ModelCardProps) {
  const [copied, setCopied] = useState(false);
  const [imageError, setImageError] = useState(false);
  const t = useTranslations('ModelCard');
  const tCommon = useTranslations('common');

  const handleCopy = () => {
    const textToCopy = model.model_name;

    // Try modern clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), COPY_FEEDBACK_DURATION);
      }).catch(() => {
        fallbackCopy(textToCopy);
      });
    } else {
      fallbackCopy(textToCopy);
    }
  };

  const fallbackCopy = (text: string) => {
    // Fallback for older browsers or non-HTTPS contexts
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      setCopied(true);
      setTimeout(() => setCopied(false), COPY_FEEDBACK_DURATION);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
    document.body.removeChild(textArea);
  };

  const handleImageError = () => {
    setImageError(true);
  };

  // 获取用户名首字母用于 AvatarFallback
  const getUserInitial = (name?: string): string => {
    if (!name) return '?';
    const parts = name.split('@');
    const username = parts[0];
    return username.charAt(0).toUpperCase();
  };

  // 获取输入/输出类型图标
  const getTypeIcon = (type: string) => {
    const IconComponent = TYPE_ICONS[type] || Type;
    return <IconComponent className="w-3 h-3" />;
  };

  // 渲染类型图标组
  const renderTypeIcons = (types: string[]) => {
    return (
      <div className="flex gap-1.5">
        {ALL_TYPES.map((type) => {
          const isSupported = types.includes(type);
          const IconComponent = TYPE_ICONS[type] || Type;
          return (
            <div
              key={type}
              title={TYPE_LABELS[type] || type}
              className={`inline-flex items-center justify-center w-6 h-6 rounded-xl border-2 transition-all ${
                isSupported
                  ? 'border-indigo-300 bg-gradient-to-br from-indigo-50 to-purple-50 text-indigo-700 shadow-sm'
                  : 'border-gray-200 bg-gray-50 text-gray-400 opacity-50'
              }`}
            >
              <IconComponent className="w-3.5 h-3.5" />
            </div>
          );
        })}
      </div>
    );
  };

  // 最多显示前 5 个头像，超出显示 "+N"
  const visibleSharers = model.shared_by.slice(0, 5);
  const extraSharersCount = Math.max(0, model.shared_by.length - 5);

  // 提供商列表（最多显示前 5 个）
  const providers = model.providers || [];
  const visibleProviders = providers.slice(0, 5);
  const extraProvidersCount = Math.max(0, providers.length - 5);

  // 获取提供商显示名称：直接使用 API 返回的 name，去掉 Coding Plan 后缀
  const getProviderDisplayName = (provider: { code: string; name: string }): string => {
    if (provider.name) {
      return provider.name.replace(/\s*Coding Plan$/i, '');
    }
    return provider.code;
  };

  return (
    <Card className="clay-card group relative overflow-hidden border-[3px] border-indigo-100">
      <CardHeader className="pb-3 bg-gradient-to-br from-white/50 to-indigo-50/50">
        <div className="flex items-start justify-between gap-3">
          {/* 左侧：头像 + 模型信息 */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            {imageError ? (
              // 默认模型图标（首字母占位符）
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-lg border-2 border-white/50">
                {model.model_name.charAt(0).toUpperCase()}
              </div>
            ) : (
              <div className="w-12 h-12 rounded-2xl flex-shrink-0 overflow-hidden shadow-lg border-2 border-white/50 bg-white p-1">
                <Image
                  src={model.model_logo_url || getModelLogo(model.model_name)}
                  alt={model.model_name}
                  width={40}
                  height={40}
                  className="w-full h-full object-contain"
                  onError={handleImageError}
                />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <CardTitle className="text-lg font-semibold text-indigo-900 truncate">{model.display_name}</CardTitle>
              <div className="flex items-center gap-2 text-sm text-indigo-600 mt-1">
                <span className="font-mono text-xs bg-indigo-100 px-2 py-0.5 rounded-lg">{model.model_name}</span>
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-xl bg-indigo-100 hover:bg-indigo-200 text-indigo-600 transition-all hover:scale-110 active:scale-95"
                  aria-label={copied ? t('ariaLabels.copied') : t('ariaLabels.copyModelName')}
                  type="button"
                >
                  {copied ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 右侧：API 按钮 */}
          {onQuickCall && (
            <Button
              onClick={() => onQuickCall(model.model_name)}
              className="clay-btn-primary h-11 w-11 p-0 rounded-xl opacity-0 group-hover:opacity-100 transition-all duration-300 flex-shrink-0"
              aria-label={t('ariaLabels.apiCall')}
              type="button"
            >
              <Code2 className="w-5 h-5" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 bg-gradient-to-br from-white to-indigo-50/30 pt-4">
        {/* 已使用 Token 和 Coding 评分 - 合并为同一行，两列布局 */}
        <div className="grid grid-cols-2 gap-3">
          {/* 已使用 Token */}
          <div className="py-3 px-4 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-100 border-2 border-blue-200/50 shadow-sm">
            <div className="text-xs font-medium text-indigo-600 mb-1">{t('tokensUsed')}</div>
            <div className="text-xl font-bold text-indigo-900">
              {model.used_tokens?.toLocaleString() || '0'}
            </div>
          </div>
          {/* Coding 评分 */}
          <div className="py-3 px-4 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-100 border-2 border-purple-200/50 shadow-sm">
            <div className="text-xs font-medium text-purple-600 mb-1">{t('codingScore')}</div>
            <div className="text-xl font-bold text-purple-900">
              {model.coding_score || t('noScore')}
            </div>
          </div>
        </div>

        {/* 模型规格 */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="flex items-center gap-2 bg-white/50 rounded-xl p-2 border border-indigo-100/50">
            <span className="font-medium text-indigo-900">{t('inputSupport')}</span>
            <span className="flex items-center gap-1.5">
              {renderTypeIcons(model.input_types)}
            </span>
          </div>
          <div className="flex items-center gap-2 bg-white/50 rounded-xl p-2 border border-indigo-100/50">
            <span className="font-medium text-indigo-900">{t('outputSupport')}</span>
            <span className="flex items-center gap-1.5">
              {renderTypeIcons(model.output_types)}
            </span>
          </div>
          <div className="flex items-center gap-2 bg-white/50 rounded-xl p-2 border border-indigo-100/50">
            <span className="font-medium text-indigo-900">{t('context')}</span>
            <span className="font-semibold text-indigo-700">{model.context_length}</span>
          </div>
          <div className="flex items-center gap-2 bg-white/50 rounded-xl p-2 border border-indigo-100/50">
            <span className="font-medium text-indigo-900">{t('maxOutput')}</span>
            <span className="font-semibold text-indigo-700">{model.max_output_length}</span>
          </div>
        </div>

        {/* 订阅信息 - 2行2列布局 */}
        <div className="grid grid-cols-2 gap-3 pt-3 border-t-2 border-indigo-100/50 text-xs">
          {/* 左侧：订阅平台 */}
          <div>
            <div className="font-medium text-indigo-600 mb-2.5">
              {t('subscriptionPlatforms')}: <span className="text-indigo-900">{model.subscription_platform_count || 0}</span>
            </div>
            <div className="flex justify-start">
              <div className="flex -space-x-1.5">
                {visibleProviders.map((provider) => (
                  <ProviderLogoTooltip key={provider.code} provider={provider} providerName={getProviderDisplayName(provider)}>
                    <div className="w-7 h-7 rounded-full border-2 border-white shadow-md overflow-hidden bg-white hover:scale-110 hover:z-10 transition-all cursor-default">
                      <Image
                        src={provider.logo_path}
                        alt={provider.code}
                        width={28}
                        height={28}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </ProviderLogoTooltip>
                ))}
                {extraProvidersCount > 0 && (
                  <div
                    className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 border-2 border-white shadow-md flex items-center justify-center text-[10px] font-semibold text-indigo-700"
                    title={t('moreProviders', { count: extraProvidersCount })}
                  >
                    +{extraProvidersCount}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 右侧：可用订阅 */}
          <div>
            <div className="font-medium text-indigo-600 mb-2.5">
              {t('availableSubscriptions')}: <span className="text-indigo-900">{model.available_subscriptions}</span>
            </div>
            <div className="flex justify-start">
              <div className="flex -space-x-1.5">
                {visibleSharers.map((sharer, idx) => (
                  <SharerAvatarTooltip key={`${sharer.user_id}-${idx}`} name={sharer.name || tCommon('unknown')}>
                    <Avatar
                      className="w-7 h-7 border-2 border-white shadow-md hover:scale-110 hover:z-10 transition-all cursor-default"
                    >
                      <AvatarImage src={sharer.avatar_url} alt={sharer.name} />
                      <AvatarFallback className="text-[10px] font-semibold bg-gradient-to-br from-indigo-100 to-purple-100 text-indigo-700">
                        {getUserInitial(sharer.name)}
                      </AvatarFallback>
                    </Avatar>
                  </SharerAvatarTooltip>
                ))}
                {extraSharersCount > 0 && (
                  <div
                    className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 border-2 border-white shadow-md flex items-center justify-center text-[10px] font-semibold text-indigo-700"
                    title={t('moreSubscriptions', { count: extraSharersCount })}
                  >
                    +{extraSharersCount}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
