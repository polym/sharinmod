'use client';

import { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ClientName } from './ClientName';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';

interface UsageLog {
  id: number;
  request_time: string;
  model_name: string;
  status: string;
  kind: string;
  unified_api_key_name: string | null;
  client: string | null;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  ttft: number | null;
  total_duration: number | null;
  num_fails: number;
  error_details?: string;
}

interface ErrorDetail {
  start_time?: number;
  error_code?: string;
  error_str?: string;
  provider?: string;
  subscription_id?: number;
}

interface UsageLogsTableProps {
  logs: UsageLog[];
  hasMore: boolean;
  onLoadMore: () => void;
  loading: boolean;
  userTimezone?: string;
}

// Map kind enum to display labels
const getKindLabelKey = (kind: string): string => {
  const normalizedKind = kind.toLowerCase();
  if (normalizedKind === 'shared') return 'typeShared';
  if (normalizedKind === 'own') return 'typeOwn';
  return 'typeDirect';
};

// Get label style based on kind
const getKindLabelStyle = (kind: string): string => {
  const normalizedKind = kind.toLowerCase();
  if (normalizedKind === 'shared') {
    return 'px-2 py-1 rounded text-sm bg-purple-100 text-purple-800';
  } else if (normalizedKind === 'own') {
    return 'px-2 py-1 rounded text-sm bg-gray-100 text-gray-800';
  }
  // direct - no background style
  return '';
};

// 错误详情弹窗组件
function ErrorDetailsDialog({ errorDetails, children }: { errorDetails?: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const t = useTranslations('usageTable');
  const { locale } = useLocaleStore();

  // 格式化错误时间戳为可读时间
  const formatErrorTime = (timestamp: number) => {
    // 处理无效时间戳（0 或负数）
    if (!timestamp || timestamp < 0) {
      return '-';
    }
    return new Date(timestamp * 1000).toLocaleString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  // 切换行展开状态
  const toggleRow = (index: number) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // 解析 error_details JSON
  const errors: ErrorDetail[] = errorDetails ? (() => {
    try {
      const parsed = JSON.parse(errorDetails);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.error('Failed to parse error_details:', e);
      return [];
    }
  })() : [];

  // 错误信息截断长度
  const TRUNCATE_LENGTH = 100;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      setOpen(isOpen);
      if (!isOpen) {
        setExpandedRows(new Set());
      }
    }}>
      <DialogTrigger asChild>
        <button type="button" className="inline-flex items-center">
          {children}
        </button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl lg:max-w-[66.67%]">
        <DialogHeader>
          <DialogTitle>{t('errorDetails')}</DialogTitle>
        </DialogHeader>
        <div className="max-h-[60vh] overflow-y-auto">
          {errors.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="whitespace-nowrap">{t('callTime')}</TableHead>
                  <TableHead className="whitespace-nowrap">{t('provider')}</TableHead>
                  <TableHead className="whitespace-nowrap">{t('errorCode')}</TableHead>
                  <TableHead className="w-[50%]">{t('errorMessage')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {errors.map((error: ErrorDetail, index: number) => {
                  const isExpanded = expandedRows.has(index);
                  const errorStr = error.error_str || '-';
                  const shouldTruncate = errorStr.length > TRUNCATE_LENGTH;

                  return (
                    <TableRow key={index}>
                      <TableCell className="text-sm whitespace-nowrap">
                        {error.start_time ? formatErrorTime(error.start_time) : '-'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {error.provider || '-'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {error.error_code || '-'}
                      </TableCell>
                      <TableCell className="text-sm">
                        <div className="flex flex-col gap-1">
                          <span className="break-all">
                            {isExpanded || !shouldTruncate
                              ? errorStr
                              : `${errorStr.slice(0, TRUNCATE_LENGTH)}...`}
                          </span>
                          {shouldTruncate && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleRow(index);
                              }}
                              aria-expanded={isExpanded}
                              aria-label={isExpanded ? t('collapse') : t('expand')}
                              className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-xs w-fit"
                            >
                              {isExpanded ? (
                                <>
                                  <ChevronUp className="w-3 h-3" />
                                  {t('collapse')}
                                </>
                              ) : (
                                <>
                                  <ChevronDown className="w-3 h-3" />
                                  {t('expand')}
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center text-gray-500 py-8">
              -
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function UsageLogsTable({ logs, hasMore, onLoadMore, loading, userTimezone }: UsageLogsTableProps) {
  const t = useTranslations('usageTable');
  const { locale } = useLocaleStore();

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: userTimezone
    });
  };

  const formatTokens = (total: number, input: number, output: number) => {
    return (
      <div>
        <div>{total.toLocaleString()}</div>
        <div className="text-xs text-gray-500">
          {input.toLocaleString()} + {output.toLocaleString()}
        </div>
      </div>
    );
  };

  const formatDuration = (total: number | null, ttft: number | null) => {
    if (total === null || total === undefined) return '-';
    return (
      <div>
        <div>{total.toFixed(2)}s</div>
        {ttft !== null && ttft !== undefined && (
          <div className="text-xs text-gray-500">
            TTFT: {ttft.toFixed(2)}s
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t('time')}</TableHead>
              <TableHead className="text-center">{t('client')}</TableHead>
              <TableHead>{t('model')}</TableHead>
              <TableHead>{t('status')}</TableHead>
              <TableHead>{t('apiKey')}</TableHead>
              <TableHead>{t('type')}</TableHead>
              <TableHead>{t('tokens')}</TableHead>
              <TableHead>{t('duration')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="text-sm">{formatTime(log.request_time)}</TableCell>
                <TableCell className="text-center">
                  <ClientName client={log.client} />
                </TableCell>
                <TableCell className="text-sm">{log.model_name}</TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded text-sm ${
                    log.status === 'success'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {log.status === 'success' ? t('statusSuccess') : t('statusFailed')}
                  </span>
                  {log.num_fails > 0 && (
                    <ErrorDetailsDialog errorDetails={log.error_details}>
                      <AlertTriangle className="ml-1 w-4 h-4 text-amber-600 cursor-pointer" />
                    </ErrorDetailsDialog>
                  )}
                </TableCell>
                <TableCell className="text-sm">
                  {log.unified_api_key_name || '-'}
                </TableCell>
                <TableCell className="text-sm">
                  <span className={getKindLabelStyle(log.kind)}>
                    {t(getKindLabelKey(log.kind))}
                  </span>
                </TableCell>
                <TableCell className="text-sm">
                  {formatTokens(log.total_tokens, log.input_tokens, log.output_tokens)}
                </TableCell>
                <TableCell className="text-sm">
                  {formatDuration(log.total_duration, log.ttft)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {hasMore && (
        <div className="text-center pt-4">
          <Button onClick={onLoadMore} variant="outline" disabled={loading}>
            {loading ? t('loadingMore') : t('loadMore')}
          </Button>
        </div>
      )}
    </div>
  );
}
