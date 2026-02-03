'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';

interface UsageLog {
  id: number;
  request_time: string;
  model_name: string;
  status: string;
  kind: string;
  unified_api_key_name: string | null;
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
  'own': '自用',
  'OWN': '自用',
  'shared': '共享',
  'SHARED': '共享',
  'direct': '直连',
  'DIRECT': '直连',
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
    return `${total} (${input} + ${output})`;
  };

  const formatDuration = (value: number | null) => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(3)} s`;
  };

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>时间</TableHead>
              <TableHead>模型</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>API Key</TableHead>
              <TableHead>类型</TableHead>
              <TableHead>Tokens</TableHead>
              <TableHead>TTFT</TableHead>
              <TableHead>总时长</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="text-sm">{formatTime(log.request_time)}</TableCell>
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
                  {kindLabelMap[log.kind] || log.kind}
                </TableCell>
                <TableCell className="text-sm">
                  {formatTokens(log.total_tokens, log.input_tokens, log.output_tokens)}
                </TableCell>
                <TableCell className="text-sm">
                  {formatDuration(log.ttft)}
                </TableCell>
                <TableCell className="text-sm">
                  {formatDuration(log.total_duration)}
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
