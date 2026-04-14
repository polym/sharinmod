'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { apiKeyAPI } from '@/lib/services';

interface UsageRecord {
  id: number;
  api_key_id: number;
  unified_api_key_id?: number;
  endpoint: string;
  method: string;
  status_code: number;
  created_at: string;
  response_time_ms?: number;
  vendor?: string;
}

export function APIKeyUsage() {
  const [usage, setUsage] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 10;

  const loadUsage = async (page = 1) => {
    try {
      const response = await apiKeyAPI.getUsageHistory({
        page: page,
        limit: PAGE_SIZE,
      });

      setUsage(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load usage:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsage();
  }, []);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages && !loading) {
      setCurrentPage(newPage);
      loadUsage(newPage);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const formatTime = (dateString: string): string => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getStatusBadgeClass = (statusCode: number): string => {
    if (statusCode >= 200 && statusCode < 300) {
      return 'bg-[#1ed760]/10 text-[#1ed760]';
    } else if (statusCode >= 400) {
      return 'bg-[#f3727f]/10 text-[#f3727f]';
    } else {
      return 'bg-[#ffa42b]/10 text-[#ffa42b]';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>API Key使用历史</CardTitle>
        <CardDescription>
          查看您的API Key使用记录和API调用历史
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8">加载中...</div>
        ) : usage.length === 0 ? (
          <div className="text-center py-8 text-[#b3b3b3]">
            暂无使用记录
          </div>
        ) : (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>请求</TableHead>
                    <TableHead>供应商</TableHead>
                    <TableHead>统一API Key ID</TableHead>
                    <TableHead>时间</TableHead>
                    <TableHead>响应时间</TableHead>
                    <TableHead>状态码</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usage.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div>
                          <span className="font-medium">{record.method}</span>
                          <span className="text-[#b3b3b3] mx-1">→</span>
                          <span className="font-mono text-sm">{record.endpoint}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {record.vendor || <span className="text-[#535353]">-</span>}
                      </TableCell>
                      <TableCell>
                        {record.unified_api_key_id || <span className="text-[#535353]">-</span>}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-[#b3b3b3]">{formatTime(record.created_at)}</span>
                      </TableCell>
                      <TableCell>
                        {record.response_time_ms ? (
                          <span className="text-sm text-[#b3b3b3]">{record.response_time_ms}ms</span>
                        ) : (
                          <span className="text-[#535353]">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded text-sm ${getStatusBadgeClass(record.status_code)}`}>
                          {record.status_code}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between gap-4 mt-6">
                <div className="text-sm text-[#b3b3b3]">
                  显示 {(currentPage - 1) * PAGE_SIZE + 1}-{Math.min(currentPage * PAGE_SIZE, total)} 条，共 {total} 条
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1 || loading}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm whitespace-nowrap px-2">
                    {currentPage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages || loading}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}