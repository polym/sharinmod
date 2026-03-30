'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuthStore } from '@/lib/store';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';
import { useToast } from '@/components/ui/toast';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface OperationLog {
  id: number;
  user_id: number;
  user_email: string | null;
  user_name: string | null;
  operation_type: string;
  resource_type: string;
  resource_id: number;
  created_at: string;
}

interface OperationLogListResponse {
  items: OperationLog[];
  total: number;
  page: number;
  page_size: number;
}

const PAGE_SIZE = 20;

export default function AdminLogsPage() {
  const router = useRouter();
  const t = useTranslations('adminLogs');
  const tCommon = useTranslations('common');
  const { locale } = useLocaleStore();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const { toast } = useToast();

  const [logs, setLogs] = useState<OperationLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  // Filter states
  const [operationTypeFilter, setOperationTypeFilter] = useState<string>('all');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('all');

  // Track pending requests to prevent race conditions
  const requestIdRef = useRef(0);
  const currentPageRef = useRef(1);

  useEffect(() => {
    currentPageRef.current = currentPage;
  }, [currentPage]);

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString(locale === 'zh-CN' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getOperationTypeLabel = (type: string) => {
    return t(`operationTypes.${type}`) || type;
  };

  const getResourceTypeLabel = (type: string) => {
    return t(`resourceTypes.${type}`) || type;
  };

  const loadLogs = useCallback(async (page: number = 1) => {
    const currentRequestId = ++requestIdRef.current;
    setLoading(true);

    try {
      const params: Record<string, string | number> = {
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      };
      if (operationTypeFilter && operationTypeFilter !== 'all') {
        params.operation_type = operationTypeFilter;
      }
      if (resourceTypeFilter && resourceTypeFilter !== 'all') {
        params.resource_type = resourceTypeFilter;
      }

      const response = await adminAPI.getOperationLogs(params);

      if (currentRequestId !== requestIdRef.current) {
        return;
      }

      const data = response.data as OperationLogListResponse;
      setLogs(data.items);
      setTotal(data.total);
      setCurrentPage(page);
    } catch (error: any) {
      if (currentRequestId !== requestIdRef.current) {
        return;
      }

      console.error('Failed to load operation logs:', error);
      toast({
        title: tCommon('error'),
        description: error.response?.data?.detail || error.message || tCommon('error'),
        variant: 'destructive',
      });
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [operationTypeFilter, resourceTypeFilter, toast, tCommon]);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    if (currentUser?.is_admin) {
      loadLogs(1);
    } else {
      router.push('/marketplace');
    }
  }, [currentUser, isAuthenticated, loadLogs, router, setShowLoginDialog]);

  useIntervalOnVisible(() => {
    if (isAuthenticated && currentUser?.is_admin && currentPageRef.current >= 1) {
      loadLogs(currentPageRef.current);
    }
  }, isAuthenticated && currentUser?.is_admin ? 30000 : null);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages && !loading) {
      loadLogs(newPage);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleOperationTypeFilterChange = (value: string) => {
    setOperationTypeFilter(value);
    setCurrentPage(1);
  };

  const handleResourceTypeFilterChange = (value: string) => {
    setResourceTypeFilter(value);
    setCurrentPage(1);
  };

  return (
    <div className="container mx-auto py-6 max-w-7xl">
      <Card>
        <CardHeader>
          <CardTitle>{t('title')}</CardTitle>
          <CardDescription>{t('description')}</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">{t('operationType')}</label>
              <Select value={operationTypeFilter} onValueChange={handleOperationTypeFilterChange}>
                <SelectTrigger>
                  <SelectValue placeholder={t('filter.operationType')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('filter.allOperations')}</SelectItem>
                  <SelectItem value="create">{t('operationTypes.create')}</SelectItem>
                  <SelectItem value="update">{t('operationTypes.update')}</SelectItem>
                  <SelectItem value="delete">{t('operationTypes.delete')}</SelectItem>
                  <SelectItem value="restart">{t('operationTypes.restart')}</SelectItem>
                  <SelectItem value="enable">{t('operationTypes.enable')}</SelectItem>
                  <SelectItem value="disable">{t('operationTypes.disable')}</SelectItem>
                  <SelectItem value="reset_password">{t('operationTypes.reset_password')}</SelectItem>
                  <SelectItem value="grant_admin">{t('operationTypes.grant_admin')}</SelectItem>
                  <SelectItem value="revoke_admin">{t('operationTypes.revoke_admin')}</SelectItem>
                  <SelectItem value="reset_token">{t('operationTypes.reset_token')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">{t('resourceType')}</label>
              <Select value={resourceTypeFilter} onValueChange={handleResourceTypeFilterChange}>
                <SelectTrigger>
                  <SelectValue placeholder={t('filter.resourceType')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('filter.allResources')}</SelectItem>
                  <SelectItem value="user">{t('resourceTypes.user')}</SelectItem>
                  <SelectItem value="claw">{t('resourceTypes.claw')}</SelectItem>
                  <SelectItem value="provider">{t('resourceTypes.provider')}</SelectItem>
                  <SelectItem value="provider_model">{t('resourceTypes.provider_model')}</SelectItem>
                  <SelectItem value="unified_api_key">{t('resourceTypes.unified_api_key')}</SelectItem>
                  <SelectItem value="shared_api_key">{t('resourceTypes.shared_api_key')}</SelectItem>
                  <SelectItem value="global_model">{t('resourceTypes.global_model')}</SelectItem>
                  <SelectItem value="system_setting">{t('resourceTypes.system_setting')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="text-center py-8">{tCommon('loading')}</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">{t('noLogs')}</div>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('timestamp')}</TableHead>
                      <TableHead>{t('operator')}</TableHead>
                      <TableHead>{t('operationType')}</TableHead>
                      <TableHead>{t('resourceType')}</TableHead>
                      <TableHead>{t('resourceId')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-mono text-sm">{formatTime(log.created_at)}</TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{log.user_name || log.user_email || `User ${log.user_id}`}</div>
                            <div className="text-sm text-muted-foreground">{log.user_email}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium">
                            {getOperationTypeLabel(log.operation_type)}
                          </span>
                        </TableCell>
                        <TableCell>{getResourceTypeLabel(log.resource_type)}</TableCell>
                        <TableCell className="font-mono">{log.resource_id}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    {t('showing', {
                      start: (currentPage - 1) * PAGE_SIZE + 1,
                      end: Math.min(currentPage * PAGE_SIZE, total),
                      total
                    })}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(1)}
                      disabled={currentPage === 1 || loading}
                    >
                      {tCommon('firstPage')}
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1 || loading}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm">
                      {t('pageInfo', { current: currentPage, total: totalPages })}
                    </span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages || loading}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(totalPages)}
                      disabled={currentPage === totalPages || loading}
                    >
                      {tCommon('lastPage')}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
