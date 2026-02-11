'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
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
                    <span
                      className="ml-1 text-amber-600 cursor-help"
                      title={t('retryTimes', { count: log.num_fails })}
                      role="tooltip"
                    >
                      !
                    </span>
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
