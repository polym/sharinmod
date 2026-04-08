'use client';

import { useEffect, useState, useMemo } from 'react';
import { ModelCard } from '@/components/ModelCard';
import { QuickCallDialog } from '@/components/QuickCallDialog';
import { modelAPI } from '@/lib/services';
import { useToast } from '@/components/ui/toast';
import { Search } from 'lucide-react';
import type { ModelInfo } from '@/types/model';
import { useTranslations } from 'next-intl';
import { useAuthStore } from '@/lib/store';

export function ModelDiscoveryPage() {
  const t = useTranslations('marketplace');
  const tToast = useTranslations('marketplace.toast');

  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  // QuickCallDialog 状态管理
  const [quickCallOpen, setQuickCallOpen] = useState(false);
  const [initialModelName, setInitialModelName] = useState<string | undefined>(undefined);
  const { toast } = useToast();
  const { currentOrganization } = useAuthStore();

  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await modelAPI.getModels(currentOrganization?.id ?? undefined);
        setModels(response.data.items);
      } catch (error: any) {
        console.error('Failed to load models:', error);

        // 区分不同类型的错误，显示更友好的错误消息
        let errorMessage = tToast('loadFailed');
        if (error.response?.status === 401) {
          errorMessage = tToast('pleaseLogin');
        } else if (error.response?.status === 403) {
          errorMessage = tToast('noPermission');
        } else if (error.response?.status === 500) {
          errorMessage = tToast('serverError');
        } else if (error.response?.status === 503) {
          errorMessage = tToast('serviceUnavailable');
        } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
          errorMessage = tToast('networkError');
        } else if (error.code === 'ECONNABORTED') {
          errorMessage = tToast('requestTimeout');
        }

        toast({
          title: tToast('error'),
          description: errorMessage,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    loadModels();
  }, [toast, tToast, currentOrganization]);

  // 使用 useMemo 缓存过滤结果，优化性能
  const filteredModels = useMemo(() => {
    const query = searchQuery.toLowerCase();
    return models.filter((model) => {
      return (
        model.display_name.toLowerCase().includes(query) ||
        model.description.toLowerCase().includes(query) ||
        model.model_name.toLowerCase().includes(query)
      );
    });
  }, [models, searchQuery]);

  // 处理打开 QuickCallDialog
  const handleQuickCallOpen = (modelName?: string) => {
    setInitialModelName(modelName);
    setQuickCallOpen(true);
  };

  // 处理关闭 QuickCallDialog
  const handleQuickCallClose = () => {
    setQuickCallOpen(false);
    setInitialModelName(undefined);
  };

  return (
    <>
      <div className="space-y-6">
        {/* 搜索栏 */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-indigo-400 w-5 h-5" />
          <input
            type="text"
            placeholder={t('searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="clay-input w-full pl-12 pr-4 py-3 border-2 border-indigo-200/50 rounded-xl bg-gradient-to-br from-white to-indigo-50/30 text-indigo-900 placeholder-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-base"
          />
        </div>

        {/* 加载状态 */}
        {loading ? (
          <div className="text-center py-12 text-indigo-600 font-medium">
            {t('loading')}
          </div>
        ) : filteredModels.length === 0 ? (
          <div className="text-center py-12 text-indigo-600 font-medium">
            {searchQuery ? t('noMatches') : t('noModels')}
          </div>
        ) : (
          /* 模型卡片网格 */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredModels.map((model) => (
              <ModelCard
                key={`${model.provider}-${model.model_name}`}
                model={model}
                onQuickCall={handleQuickCallOpen}
              />
            ))}
          </div>
        )}
      </div>

      {/* QuickCallDialog - 受控模式 */}
      <QuickCallDialog
        open={quickCallOpen}
        onOpenChange={(open) => {
          if (!open) {
            handleQuickCallClose();
          } else {
            setQuickCallOpen(true);
          }
        }}
        initialModelName={initialModelName}
      />
    </>
  );
}
