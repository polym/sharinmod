'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Copy, Check } from 'lucide-react';
import Image from 'next/image';
import { getProviderLogo } from '@/lib/providers';
import type { SharedBy } from '@/types/model';

const COPY_FEEDBACK_DURATION = 1500; // ms

interface ModelCardProps {
  model: {
    display_name: string;
    model_name: string; // 原始模型名称，如 "glm-4.7"（显示为「模型 ID」）
    description: string;
    input_type: string;
    output_type: string;
    context_length: string;
    max_output_length: string;
    available_subscriptions: number;
    shared_by: SharedBy[];
    provider: string;
  };
}

export function ModelCard({ model }: ModelCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(model.model_name);
        setCopied(true);
        setTimeout(() => setCopied(false), COPY_FEEDBACK_DURATION);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  // 获取用户名首字母用于 AvatarFallback
  const getUserInitial = (name?: string): string => {
    if (!name) return '?';
    const parts = name.split('@');
    const username = parts[0];
    return username.charAt(0).toUpperCase();
  };

  // 最多显示前 3 个头像，超出显示 "+N"
  const visibleSharers = model.shared_by.slice(0, 3);
  const extraCount = Math.max(0, model.shared_by.length - 3);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <Image
              src={getProviderLogo(model.provider)}
              alt={model.provider}
              width={32}
              height={32}
              className="flex-shrink-0"
            />
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
                    <Check className="w-3 h-3 text-green-600" />
                  ) : (
                    <Copy className="w-3 h-3 text-gray-500" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 描述 */}
        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
          {model.description}
        </p>

        {/* 模型规格 */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">输入:</span>
            <span className="font-medium">{model.input_type}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">输出:</span>
            <span className="font-medium">{model.output_type}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">上下文:</span>
            <span className="font-medium">{model.context_length}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500 dark:text-gray-400">输出:</span>
            <span className="font-medium">{model.max_output_length}</span>
          </div>
        </div>

        {/* 共享者和订阅数 */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center">
            <div className="flex -space-x-2">
              {visibleSharers.map((sharer) => (
                <Avatar key={sharer.user_id} className="w-7 h-7 border-2 border-white dark:border-gray-800">
                  <AvatarImage src={sharer.avatar_url} alt={sharer.name} />
                  <AvatarFallback className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-300">
                    {getUserInitial(sharer.name)}
                  </AvatarFallback>
                </Avatar>
              ))}
              {extraCount > 0 && (
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 border-2 border-white dark:border-gray-800 flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-400">
                  +{extraCount}
                </div>
              )}
            </div>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {model.available_subscriptions} {model.available_subscriptions === 1 ? '订阅' : '订阅'}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
