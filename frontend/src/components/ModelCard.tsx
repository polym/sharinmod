'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Copy, Check, Type, Image as ImageIcon, Video, Mic, Code2, File } from 'lucide-react';
import Image from 'next/image';
import { getModelLogo } from '@/lib/providers';
import type { SharedBy } from '@/types/model';

const COPY_FEEDBACK_DURATION = 1500; // ms

interface ModelCardProps {
  model: {
    display_name: string;
    model_name: string; // 原始模型名称，如 "glm-4.7"（显示为「模型 ID」）
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
    providers?: Array<{ code: string; logo_path: string }>;
    subscription_platform_count?: number;
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

// 输入/输出类型中文标签映射
const TYPE_LABELS: Record<string, string> = {
  'Text': '文本',
  'Image': '图片',
  'Video': '视频',
  'Audio': '音频',
  'File': '文件',
};

// 所有支持的类型（用于显示完整类型栏）
const ALL_TYPES = ['Text', 'Image', 'Video', 'Audio', 'File'] as const;

// 提供商名称映射
const PROVIDER_NAMES: Record<string, string> = {
  'bigmodel': '智谱',
  'z.ai': 'Z.AI',
  'volcengine': '火山引擎',
};

export function ModelCard({ model, onQuickCall }: ModelCardProps) {
  const [copied, setCopied] = useState(false);
  const [imageError, setImageError] = useState(false);

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
      <div className="flex gap-1">
        {ALL_TYPES.map((type) => {
          const isSupported = types.includes(type);
          const IconComponent = TYPE_ICONS[type] || Type;
          return (
            <div
              key={type}
              title={TYPE_LABELS[type] || type}
              className="inline-flex"
            >
              <IconComponent
                className={`w-3 h-3 ${isSupported ? 'text-gray-700 dark:text-gray-300' : 'text-gray-300 dark:text-gray-600 opacity-50'}`}
              />
            </div>
          );
        })}
      </div>
    );
  };

  // 最多显示前 3 个头像，超出显示 "+N"
  const visibleSharers = model.shared_by.slice(0, 3);
  const extraSharersCount = Math.max(0, model.shared_by.length - 3);

  // 提供商列表（最多显示前 3 个）
  const providers = model.providers || [];
  const visibleProviders = providers.slice(0, 3);
  const extraProvidersCount = Math.max(0, providers.length - 3);

  return (
    <Card className="group hover:shadow-md transition-shadow relative">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          {/* 左侧：头像 + 模型信息 */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {imageError ? (
              // 默认模型图标（首字母占位符）
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                {model.model_name.charAt(0).toUpperCase()}
              </div>
            ) : (
              <Image
                src={getModelLogo(model.model_name)}
                alt={model.model_name}
                width={40}
                height={40}
                className="flex-shrink-0 rounded-lg object-contain"
                onError={handleImageError}
              />
            )}
            <div className="min-w-0 flex-1">
              <CardTitle className="text-lg truncate">{model.display_name}</CardTitle>
              <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                <span className="font-mono text-xs">{model.model_name}</span>
                <button
                  onClick={handleCopy}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  aria-label={copied ? '已复制' : '复制模型名称'}
                  type="button"
                >
                  {copied ? (
                    <Check className="w-3 h-3 text-purple-600" />
                  ) : (
                    <Copy className="w-3 h-3 text-gray-500" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 右侧：API 按钮 */}
          {onQuickCall && (
            <Button
              onClick={() => onQuickCall(model.model_name)}
              className="h-10 w-10 p-0 rounded-full bg-purple-500 hover:bg-purple-600 text-white opacity-0 group-hover:opacity-100 transition-opacity shadow-md flex-shrink-0"
              aria-label="API 调用"
              type="button"
            >
              <Code2 className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 已使用 Token 和 Coding 评分 - 合并为同一行，两列布局 */}
        <div className="grid grid-cols-2 gap-3">
          {/* 已使用 Token */}
          <div className="py-2 px-3 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950/30 dark:to-blue-900/30 rounded-lg">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">已使用 Token</div>
            <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {model.used_tokens?.toLocaleString() || '0'}
            </div>
          </div>
          {/* Coding 评分 */}
          <div className="py-2 px-3 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950/30 dark:to-purple-900/30 rounded-lg">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Coding 评分</div>
            <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {model.coding_score || '暂无'}
            </div>
          </div>
        </div>

        {/* 模型规格 */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">输入支持:</span>
            <span className="font-medium flex items-center gap-1">
              {renderTypeIcons(model.input_types)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">输出支持:</span>
            <span className="font-medium flex items-center gap-1">
              {renderTypeIcons(model.output_types)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">上下文:</span>
            <span className="font-medium">{model.context_length}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">最大输出:</span>
            <span className="font-medium">{model.max_output_length}</span>
          </div>
        </div>

        {/* 订阅信息 - 2行2列布局 */}
        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100 dark:border-gray-800 text-xs">
          {/* 左侧：订阅平台 */}
          <div>
            <div className="text-gray-500 dark:text-gray-400 mb-2">
              订阅平台：{model.subscription_platform_count || 0}
            </div>
            <div className="flex justify-start">
              <div className="flex -space-x-1">
                {visibleProviders.map((provider) => (
                  <div
                    key={provider.code}
                    className="w-6 h-6 rounded-full border-2 border-white dark:border-gray-800 overflow-hidden bg-white hover:scale-110 transition-transform cursor-help"
                    title={PROVIDER_NAMES[provider.code] || provider.code}
                  >
                    <Image
                      src={provider.logo_path}
                      alt={provider.code}
                      width={24}
                      height={24}
                    />
                  </div>
                ))}
                {extraProvidersCount > 0 && (
                  <div
                    className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 border-2 border-white dark:border-gray-800 flex items-center justify-center text-[10px] font-medium text-gray-600 dark:text-gray-400"
                    title={`还有 ${extraProvidersCount} 个平台`}
                  >
                    +{extraProvidersCount}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 右侧：可用订阅 */}
          <div>
            <div className="text-gray-500 dark:text-gray-400 mb-2">
              可用订阅：{model.available_subscriptions}
            </div>
            <div className="flex justify-start">
              <div className="flex -space-x-1">
                {visibleSharers.map((sharer) => (
                  <Avatar
                    key={sharer.user_id}
                    className="w-6 h-6 border-2 border-white dark:border-gray-800 hover:scale-110 transition-transform cursor-help"
                    title={sharer.name || `用户 ${sharer.user_id}`}
                  >
                    <AvatarImage src={sharer.avatar_url} alt={sharer.name} />
                    <AvatarFallback className="text-[10px] bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-300">
                      {getUserInitial(sharer.name)}
                    </AvatarFallback>
                  </Avatar>
                ))}
                {extraSharersCount > 0 && (
                  <div
                    className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 border-2 border-white dark:border-gray-800 flex items-center justify-center text-[10px] font-medium text-gray-600 dark:text-gray-400"
                    title={`还有 ${extraSharersCount} 个订阅`}
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
