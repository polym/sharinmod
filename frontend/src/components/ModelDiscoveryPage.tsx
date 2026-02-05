'use client';

import { useEffect, useState, useMemo } from 'react';
import { ModelCard } from '@/components/ModelCard';
import { QuickCallDialog } from '@/components/QuickCallDialog';
import { modelAPI } from '@/lib/services';
import { useToast } from '@/components/ui/toast';
import { Search } from 'lucide-react';
import type { ModelInfo } from '@/types/model';

export function ModelDiscoveryPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  // QuickCallDialog 状态管理
  const [quickCallOpen, setQuickCallOpen] = useState(false);
  const [initialModelName, setInitialModelName] = useState<string | undefined>(undefined);
  const { toast } = useToast();

  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await modelAPI.getModels();
        setModels(response.data.items);
      } catch (error: any) {
        console.error('Failed to load models:', error);

        // 区分不同类型的错误，显示更友好的错误消息
        let errorMessage = '加载模型列表失败';
        if (error.response?.status === 401) {
          errorMessage = '请先登录';
        } else if (error.response?.status === 403) {
          errorMessage = '没有权限访问';
        } else if (error.response?.status === 500) {
          errorMessage = '服务器错误，请稍后重试';
        } else if (error.response?.status === 503) {
          errorMessage = '服务暂时不可用';
        } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
          errorMessage = '网络连接失败';
        } else if (error.code === 'ECONNABORTED') {
          errorMessage = '请求超时';
        }

        toast({
          title: '错误',
          description: errorMessage,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    loadModels();
  }, [toast]);

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
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="搜索模型名称或描述..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        {/* 加载状态 */}
        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            加载中...
          </div>
        ) : filteredModels.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            {searchQuery ? '未找到匹配的模型' : '暂无可用的模型'}
          </div>
        ) : (
          /* 模型卡片网格 */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
