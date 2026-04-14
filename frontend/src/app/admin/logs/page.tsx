'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuthStore } from '@/lib/store';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';
import { useToast } from '@/components/ui/toast';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';
import { ChevronLeft, ChevronRight, History, ArrowUpDown, Search, X } from 'lucide-react';

interface OperationLog {
  id: number;
  user_id: number;
  user_email: string | null;
  user_name: string | null;
  operation_type: string;
  resource_type: string;
  resource_id: number;
  resource_name: string | null;
  created_at: string;
}

interface OperationLogListResponse {
  items: OperationLog[];
  total: number;
  page: number;
  page_size: number;
}

const PAGE_SIZE = 10;

// 操作类型颜色映射
const getOperationTypeStyle = (type: string): string => {
  const styles: Record<string, string> = {
    create: 'bg-[#1ed760]/10 text-[#1ed760] border border-[#1ed760]/30',
    update: 'bg-blue-500/10 text-blue-400 border border-blue-500/30',
    delete: 'bg-red-500/10 text-[#f3727f] border border-red-500/30',
    restart: 'bg-orange-500/10 text-orange-400 border border-orange-500/30',
    enable: 'bg-[#1ed760]/10 text-[#1ed760] border border-[#1ed760]/30',
    disable: 'bg-[#535353]/20 text-[#b3b3b3] border border-[#4d4d4d]',
    reset_password: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
    grant_admin: 'bg-[#1ed760]/10 text-[#1ed760] border border-[#1ed760]/30',
    revoke_admin: 'bg-[#1ed760]/10 text-[#1ed760] border border-[#1ed760]/30',
    reset_token: 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30',
  };
  return styles[type] || 'bg-[#282828] text-[#b3b3b3] border border-[#4d4d4d]';
};

export default function AdminLogsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const t = useTranslations('adminLogs');
  const tCommon = useTranslations('common');
  const { locale } = useLocaleStore();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const { toast } = useToast();

  const [logs, setLogs] = useState<OperationLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter states
  const [operationTypeFilter, setOperationTypeFilter] = useState<string>('all');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('all');

  // 排序状态
  const [sortField, setSortField] = useState<'created_at' | 'operation_type' | 'resource_type'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Track pending requests to prevent race conditions
  const requestIdRef = useRef(0);
  const currentPageRef = useRef(1);

  // 从 URL 读取初始状态
  useEffect(() => {
    const page = parseInt(searchParams.get('page') || '1');
    const operationType = searchParams.get('operation_type') || 'all';
    const resourceType = searchParams.get('resource_type') || 'all';
    const search = searchParams.get('search') || '';
    const sort = searchParams.get('sort') as 'created_at' | 'operation_type' | 'resource_type' | null;
    const order = searchParams.get('order') as 'asc' | 'desc' | null;

    setCurrentPage(page);
    setOperationTypeFilter(operationType);
    setResourceTypeFilter(resourceType);
    setSearchQuery(search);
    if (sort) setSortField(sort);
    if (order) setSortOrder(order);
  }, [searchParams]);

  // 更新 URL
  const updateURL = useCallback((params: Record<string, string | number>) => {
    const urlParams = new URLSearchParams(searchParams);
    Object.entries(params).forEach(([key, value]) => {
      if (value === 'all' || value === '' || value === 'created_at' || value === 'desc') {
        urlParams.delete(key);
      } else {
        urlParams.set(key, String(value));
      }
    });
    router.replace(`?${urlParams.toString()}`, { scroll: false });
  }, [searchParams, router]);

  // 同步状态到 URL
  useEffect(() => {
    updateURL({
      page: currentPage,
      operation_type: operationTypeFilter,
      resource_type: resourceTypeFilter,
      search: searchQuery,
      sort: sortField,
      order: sortOrder,
    });
  }, [currentPage, operationTypeFilter, resourceTypeFilter, searchQuery, sortField, sortOrder, updateURL]);

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
        sort_by: sortField,
        sort_order: sortOrder,
      };
      if (operationTypeFilter && operationTypeFilter !== 'all') {
        params.operation_type = operationTypeFilter;
      }
      if (resourceTypeFilter && resourceTypeFilter !== 'all') {
        params.resource_type = resourceTypeFilter;
      }
      if (searchQuery) {
        params.search = searchQuery;
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
        setIsInitialLoad(false);
      }
    }
  }, [operationTypeFilter, resourceTypeFilter, searchQuery, sortField, sortOrder, toast, tCommon]);

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

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handleSort = (field: 'created_at' | 'operation_type' | 'resource_type') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const handleClearFilters = () => {
    setOperationTypeFilter('all');
    setResourceTypeFilter('all');
    setSearchQuery('');
    setCurrentPage(1);
  };

  const hasActiveFilters = operationTypeFilter !== 'all' || resourceTypeFilter !== 'all' || searchQuery !== '';

  // Skeleton rows for loading state
  const renderSkeletonRows = () => (
    <>
      {[...Array(5)].map((_, i) => (
        <TableRow key={i}>
          <TableCell><Skeleton className="h-4 w-32" /></TableCell>
          <TableCell><Skeleton className="h-4 w-40" /></TableCell>
          <TableCell><Skeleton className="h-6 w-20" /></TableCell>
          <TableCell><Skeleton className="h-4 w-24" /></TableCell>
          <TableCell><Skeleton className="h-4 w-36" /></TableCell>
        </TableRow>
      ))}
    </>
  );

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t('title')}</CardTitle>
          <CardDescription>{t('description')}</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search & Filters */}
          <div className="flex gap-3 mb-6">
            {/* Search bar */}
            <div className="relative flex-[2]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t('filter.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10"
              />
              {searchQuery && (
                <button
                  onClick={() => handleSearchChange('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Operation Type Filter */}
            <div className="flex-1">
              <Select value={operationTypeFilter} onValueChange={handleOperationTypeFilterChange}>
                <SelectTrigger>
                  <SelectValue placeholder={t('filter.allOperations')} />
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

            {/* Resource Type Filter */}
            <div className="flex-1">
              <Select value={resourceTypeFilter} onValueChange={handleResourceTypeFilterChange}>
                <SelectTrigger>
                  <SelectValue placeholder={t('filter.allResources')} />
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

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <Button
                variant="outline"
                onClick={handleClearFilters}
                size="icon"
                title={t('filter.clearFilters')}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50 select-none group"
                    onClick={() => handleSort('created_at')}
                  >
                    <div className="flex items-center gap-1">
                      {t('timestamp')}
                      <ArrowUpDown className={`h-4 w-4 opacity-0 group-hover:opacity-50 transition-opacity ${
                        sortField === 'created_at' ? 'opacity-100' : ''
                      }`} />
                    </div>
                  </TableHead>
                  <TableHead>{t('operator')}</TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50 select-none group"
                    onClick={() => handleSort('operation_type')}
                  >
                    <div className="flex items-center gap-1">
                      {t('operationType')}
                      <ArrowUpDown className={`h-4 w-4 opacity-0 group-hover:opacity-50 transition-opacity ${
                        sortField === 'operation_type' ? 'opacity-100' : ''
                      }`} />
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50 select-none group"
                    onClick={() => handleSort('resource_type')}
                  >
                    <div className="flex items-center gap-1">
                      {t('resourceType')}
                      <ArrowUpDown className={`h-4 w-4 opacity-0 group-hover:opacity-50 transition-opacity ${
                        sortField === 'resource_type' ? 'opacity-100' : ''
                      }`} />
                    </div>
                  </TableHead>
                  <TableHead>{t('resourceName')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isInitialLoad && loading ? (
                  renderSkeletonRows()
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12">
                      <div className="flex flex-col items-center justify-center space-y-4">
                        <History className="h-12 w-12 text-muted-foreground" />
                        <div className="space-y-2">
                          <p className="text-muted-foreground">{t('noLogs')}</p>
                          {hasActiveFilters && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={handleClearFilters}
                            >
                              {t('filter.clearFilters')}
                            </Button>
                          )}
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id} className="hover:bg-muted/50 transition-colors duration-150">
                      <TableCell className="font-mono text-sm">{formatTime(log.created_at)}</TableCell>
                      <TableCell>
                        <span className="font-medium">{log.user_email || `User ${log.user_id}`}</span>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center rounded px-2.5 py-1 text-sm font-medium transition-colors ${getOperationTypeStyle(log.operation_type)}`}>
                          {getOperationTypeLabel(log.operation_type)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {getResourceTypeLabel(log.resource_type)}
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">{log.resource_name || '-'}</span>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between gap-4 mt-6">
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
                  size="icon"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1 || loading}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm whitespace-nowrap px-2">
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
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}