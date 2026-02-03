'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ClientName } from './ClientName';

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
}

interface UsageLogsTableProps {
  logs: UsageLog[];
  hasMore: boolean;
  onLoadMore: () => void;
  loading: boolean;
  userTimezone?: string;
}

// Map kind enum to Chinese display (support both lowercase and uppercase)
const kindLabelMap: Record<string, string> = {
  'own': '自有',
  'OWN': '自有',
  'shared': '外援',
  'SHARED': '外援',
  'direct': '直连',
  'DIRECT': '直连',
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
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
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
              <TableHead>时间</TableHead>
              <TableHead className="text-center">客户端</TableHead>
              <TableHead>模型</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>API Key</TableHead>
              <TableHead>类型</TableHead>
              <TableHead>Tokens</TableHead>
              <TableHead>总时长</TableHead>
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
                    {log.status === 'success' ? '成功' : '失败'}
                  </span>
                </TableCell>
                <TableCell className="text-sm">
                  {log.unified_api_key_name || '-'}
                </TableCell>
                <TableCell className="text-sm">
                  <span className={getKindLabelStyle(log.kind)}>
                    {kindLabelMap[log.kind] || log.kind}
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
            {loading ? '加载中...' : '加载更多'}
          </Button>
        </div>
      )}
    </div>
  );
}
