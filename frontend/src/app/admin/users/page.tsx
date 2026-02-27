'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, ShieldOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuthStore } from '@/lib/store';
import type { User } from '@/lib/store';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';
import { useToast } from '@/components/ui/toast';

interface UserListResponse {
  items: User[];
  total: number;
}

const PAGE_SIZE = 20;

export default function AdminUsersPage() {
  const router = useRouter();
  const t = useTranslations('adminUsers');
  const tCommon = useTranslations('common');
  const { locale } = useLocaleStore();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const { toast } = useToast();

  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [roleFilter, setRoleFilter] = useState<'all' | 'admin' | 'user'>('all');

  // Track pending requests to prevent race conditions
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    if (currentUser?.is_admin) {
      loadUsers(0, false);
    } else {
      router.push('/marketplace');
    }
  }, [currentUser, isAuthenticated, roleFilter]);

  const loadUsers = useCallback(async (offset: number = 0, append: boolean = false) => {
    // Increment request ID for this request
    const currentRequestId = ++requestIdRef.current;

    if (offset === 0) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const response = await adminAPI.getUsers({
        offset,
        limit: PAGE_SIZE,
        role_filter: roleFilter
      });

      // Ignore stale responses
      if (currentRequestId !== requestIdRef.current) {
        return;
      }

      const data = response.data as UserListResponse;

      if (append) {
        setUsers(prev => [...prev, ...data.items]);
      } else {
        setUsers(data.items);
      }

      setTotal(data.total);
      setHasMore(offset + data.items.length < data.total);
    } catch (error: any) {
      // Ignore stale errors
      if (currentRequestId !== requestIdRef.current) {
        return;
      }

      console.error('Failed to load users:', error);
      toast({
        title: tCommon('error'),
        description: error.response?.data?.detail || error.message || tCommon('error'),
        variant: 'destructive',
      });
    } finally {
      // Ignore stale finally
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
        setLoadingMore(false);
      }
    }
  }, [roleFilter, toast, tCommon]);

  const handleLoadMore = () => {
    if (!loadingMore && !loading) {
      loadUsers(users.length, true);
    }
  };

  const handleRoleFilterChange = (value: string) => {
    setRoleFilter(value as 'all' | 'admin' | 'user');
    setUsers([]);
    setHasMore(false);
  };

  const handleGrantAdmin = async (userId: number) => {
    try {
      await adminAPI.grantAdmin(userId);
      toast({
        title: tCommon('success'),
        description: t('grantSuccess'),
      });
      // Optimistically update user in list
      setUsers(prev => prev.map(u =>
        u.id === userId ? { ...u, is_admin: true } : u
      ));
    } catch (error: any) {
      console.error('Failed to grant admin:', error);
      toast({
        title: tCommon('error'),
        description: error.response?.data?.detail || t('grantFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleRevokeAdmin = async (userId: number) => {
    try {
      await adminAPI.revokeAdmin(userId);
      toast({
        title: tCommon('success'),
        description: t('revokeSuccess'),
      });
      // Optimistically update user in list
      setUsers(prev => prev.map(u =>
        u.id === userId ? { ...u, is_admin: false } : u
      ));
    } catch (error: any) {
      console.error('Failed to revoke admin:', error);
      toast({
        title: tCommon('error'),
        description: error.response?.data?.detail || t('revokeFailed'),
        variant: 'destructive',
      });
    }
  };

  const formatTokens = (tokens: number): string => {
    if (tokens < 1000) {
      return tokens.toLocaleString();
    } else if (tokens < 1000000) {
      return (tokens / 1000).toFixed(1) + 'K';
    } else if (tokens < 1000000000) {
      return (tokens / 1000000).toFixed(1) + 'M';
    } else {
      return (tokens / 1000000000).toFixed(1) + 'B';
    }
  };

  const formatTime = (dateString: string | undefined): string => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  if (!currentUser?.is_admin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Access denied</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-6">
      <Card>
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-1.5">
              <CardTitle>{t('title')}</CardTitle>
              <CardDescription>{t('description')}</CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">{t('role')}:</span>
              <Select value={roleFilter} onValueChange={handleRoleFilterChange}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('roleFilter.all')}</SelectItem>
                  <SelectItem value="admin">{t('roleFilter.admin')}</SelectItem>
                  <SelectItem value="user">{t('roleFilter.user')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">{tCommon('loading')}</div>
          ) : users.length === 0 ? (
            <div className="text-center py-8 text-gray-500">{t('noUsers')}</div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('email')}</TableHead>
                      <TableHead className="text-right">{t('subscriptions')}</TableHead>
                      <TableHead className="text-right">{t('consumedTokens')}</TableHead>
                      <TableHead className="text-right">{t('contributedTokens')}</TableHead>
                      <TableHead>{t('createdAt')}</TableHead>
                      <TableHead>{t('lastUsedAt')}</TableHead>
                      <TableHead>{t('actions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium flex items-center gap-1.5">
                              {u.email}
                              {u.is_admin && (
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-orange-500 text-white flex-shrink-0">
                                  Admin
                                </span>
                              )}
                            </span>
                            {u.name && (
                              <span className="text-xs text-gray-500">{u.name}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {u.active_subscription_count ?? 0}/{u.subscription_count ?? 0}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatTokens(u.consumed_tokens || 0)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatTokens(u.contributed_tokens || 0)}
                        </TableCell>
                        <TableCell>
                          {formatTime(u.created_at)}
                        </TableCell>
                        <TableCell>
                          {formatTime(u.last_used_at)}
                        </TableCell>
                        <TableCell>
                          {u.id !== currentUser?.id && (
                            <Button
                              onClick={() => u.is_admin ? handleRevokeAdmin(u.id!) : handleGrantAdmin(u.id!)}
                              size="sm"
                              variant="ghost"
                              aria-label={u.is_admin ? 'Revoke admin' : 'Grant admin'}
                            >
                              {u.is_admin ? (
                                <ShieldOff className="w-4 h-4" />
                              ) : (
                                <Shield className="w-4 h-4" />
                              )}
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {hasMore && (
                <div className="text-center pt-4">
                  <Button onClick={handleLoadMore} variant="outline" disabled={loadingMore}>
                    {loadingMore ? t('loadingMore') : t('loadMore')}
                  </Button>
                </div>
              )}

              <div className="text-sm text-gray-500 text-center pt-2">
                {tCommon('loading') !== 'Loading...' && `共 ${total} 位用户`}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
