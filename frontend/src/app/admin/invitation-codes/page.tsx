'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Copy, Check, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/lib/store';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';
import { useToast } from '@/components/ui/toast';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';

interface InvitationCode {
  id: number;
  code: string;
  created_by_user_id: number | null;
  used_by_user_id: number | null;
  used_at: string | null;
  created_at: string;
  is_used: boolean;
  created_by_email: string | null;
  used_by_email: string | null;
}

interface InvitationCodesResponse {
  codes: InvitationCode[];
}

export default function AdminInvitationCodesPage() {
  const router = useRouter();
  const t = useTranslations('adminInvitationCodes');
  const tCommon = useTranslations('common');
  const { locale } = useLocaleStore();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const { toast } = useToast();

  const [codes, setCodes] = useState<InvitationCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'all' | 'unused' | 'used'>('all');

  // Create dialog state
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createCount, setCreateCount] = useState(1);
  const [createLoading, setCreateLoading] = useState(false);

  // Delete confirmation dialog state
  const [showDeleteConfirmDialog, setShowDeleteConfirmDialog] = useState(false);
  const [targetCode, setTargetCode] = useState<InvitationCode | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Copy success dialog state
  const [showCopySuccessDialog, setShowCopySuccessDialog] = useState(false);
  const [copiedLink, setCopiedLink] = useState('');
  const [copied, setCopied] = useState(false);

  // Track pending requests to prevent race conditions
  const requestIdRef = useRef(0);

  const loadInvitationCodes = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;
    setLoading(true);

    try {
      const response = await adminAPI.getInvitationCodes();

      // Ignore stale responses
      if (currentRequestId !== requestIdRef.current) {
        return;
      }

      const data = response.data as InvitationCodesResponse;
      setCodes(data.codes);
    } catch (error: any) {
      // Ignore stale errors
      if (currentRequestId !== requestIdRef.current) {
        return;
      }

      console.error('Failed to load invitation codes:', error);
      toast({
        title: tCommon('error'),
        description: error.response?.data?.detail || error.message || t('loadFailed'),
        variant: 'destructive',
      });
    } finally {
      // Ignore stale finally
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [toast, tCommon, t]);

  // 初始加载
  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    if (currentUser?.is_admin) {
      loadInvitationCodes();
    } else {
      router.push('/marketplace');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser, isAuthenticated]);

  // Auto-refresh invitation codes every 30 seconds when page is visible
  useIntervalOnVisible(() => {
    if (isAuthenticated && currentUser?.is_admin) {
      loadInvitationCodes();
    }
  }, isAuthenticated && currentUser?.is_admin ? 30000 : null);

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value as 'all' | 'unused' | 'used');
  };

  const getFilteredCodes = () => {
    switch (statusFilter) {
      case 'unused':
        return codes.filter(c => !c.is_used);
      case 'used':
        return codes.filter(c => c.is_used);
      default:
        return codes;
    }
  };

  const handleCreate = async () => {
    if (createCount < 1 || createCount > 10) {
      toast({
        title: tCommon('error'),
        description: t('countRangeError'),
        variant: 'destructive',
      });
      return;
    }

    setCreateLoading(true);
    try {
      await adminAPI.createInvitationCodes(createCount);

      toast({
        title: tCommon('success'),
        description: t('createSuccess'),
      });

      // Reset form and reload
      setCreateCount(1);
      setShowCreateDialog(false);
      loadInvitationCodes();
    } catch (error: any) {
      console.error('Failed to create invitation codes:', error);
      toast({
        title: tCommon('error'),
        description: error.response?.data?.detail || error.message || t('createFailed'),
        variant: 'destructive',
      });
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!targetCode) return;

    const deletedCode = targetCode;
    setDeleteLoading(true);
    setShowDeleteConfirmDialog(false);

    // Optimistically remove code from list
    setCodes(prev => prev.filter(c => c.id !== deletedCode.id));
    setTargetCode(null);

    try {
      await adminAPI.deleteInvitationCode(deletedCode.id);
      toast({
        title: tCommon('success'),
        description: t('deleteSuccess'),
      });
    } catch (error: any) {
      // Rollback: add the deleted code back to the list
      setCodes(prev => [...prev, deletedCode].sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ));

      console.error('Failed to delete invitation code:', error);
      const errorMessage = error.response?.data?.detail || error.message || t('deleteFailed');
      toast({
        title: tCommon('error'),
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setDeleteLoading(false);
    }
  };

  const openDeleteConfirm = (code: InvitationCode) => {
    setTargetCode(code);
    setShowDeleteConfirmDialog(true);
  };

  const handleCopyLink = (code: string) => {
    const link = `${window.location.origin}/?showLogin=true&tab=register&inviteCode=${code}`;
    setCopiedLink(link);

    const copyToClipboard = async () => {
      // Fallback: 使用传统方法
      const textArea = document.createElement('textarea');
      textArea.value = link;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setShowCopySuccessDialog(true);
      setTimeout(() => setCopied(false), 2000);
      toast({
        title: t('copySuccess'),
        description: t('copySuccessDesc'),
      });
    };

    // 检查 clipboard API 是否可用
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        navigator.clipboard.writeText(link);
        setCopied(true);
        setShowCopySuccessDialog(true);
        setTimeout(() => setCopied(false), 2000);
        toast({
          title: t('copySuccess'),
          description: t('copySuccessDesc'),
        });
      } catch (error) {
        console.error('Clipboard API failed, using fallback:', error);
        copyToClipboard();
      }
    } else {
      // clipboard API 不可用，直接使用 fallback
      copyToClipboard();
    }
  };

  const formatTime = (dateString: string | undefined): string => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    } catch (error) {
      console.error('Invalid date format:', dateString, error);
      return '-';
    }
  };

  if (!currentUser?.is_admin) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="text-[#b3b3b3]">Access denied</div>
      </div>
    );
  }

  const filteredCodes = getFilteredCodes();

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
              <span className="text-sm text-[#b3b3b3]">{t('filter.all')}:</span>
              <Select value={statusFilter} onValueChange={handleStatusFilterChange}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('filter.all')}</SelectItem>
                  <SelectItem value="unused">{t('filter.unused')}</SelectItem>
                  <SelectItem value="used">{t('filter.used')}</SelectItem>
                </SelectContent>
              </Select>
              <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    {t('createTitle')}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t('createTitle')}</DialogTitle>
                    <DialogDescription>{t('createDescription')}</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="count">{t('countLabel')}</Label>
                      <Input
                        id="count"
                        type="number"
                        min="1"
                        max="10"
                        step="1"
                        value={createCount}
                        onChange={(e) => {
                          const value = parseInt(e.target.value);
                          if (!isNaN(value) && value >= 1 && value <= 10) {
                            setCreateCount(value);
                          }
                        }}
                        placeholder={t('countPlaceholder')}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                      {tCommon('cancel')}
                    </Button>
                    <Button onClick={handleCreate} disabled={createLoading}>
                      {createLoading ? tCommon('loading') : tCommon('confirm')}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">{tCommon('loading')}</div>
          ) : filteredCodes.length === 0 ? (
            <div className="text-center py-8 text-[#b3b3b3]">{t('noCodes')}</div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('code')}</TableHead>
                      <TableHead>{t('status')}</TableHead>
                      <TableHead>{t('createdBy')}</TableHead>
                      <TableHead>{t('usedBy')}</TableHead>
                      <TableHead>{t('createdAt')}</TableHead>
                      <TableHead>{t('usedAt')}</TableHead>
                      <TableHead>{t('actions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredCodes.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="font-mono">{c.code}</TableCell>
                        <TableCell>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            c.is_used
                              ? 'bg-green-500/20 text-green-500'
                              : 'bg-yellow-500/20 text-yellow-500'
                          }`}>
                            {c.is_used ? t('statusUsed') : t('statusUnused')}
                          </span>
                        </TableCell>
                        <TableCell>{c.created_by_email || '-'}</TableCell>
                        <TableCell>{c.used_by_email || '-'}</TableCell>
                        <TableCell>{formatTime(c.created_at)}</TableCell>
                        <TableCell>{formatTime(c.used_at || undefined)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            {!c.is_used && (
                              <>
                                <Button
                                  onClick={() => handleCopyLink(c.code)}
                                  size="sm"
                                  variant="ghost"
                                  aria-label={t('copyLink')}
                                >
                                  <Copy className="w-4 h-4" />
                                </Button>
                                <Button
                                  onClick={() => openDeleteConfirm(c)}
                                  size="sm"
                                  variant="ghost"
                                  aria-label={tCommon('delete')}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirmDialog} onOpenChange={setShowDeleteConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{tCommon('delete')}</DialogTitle>
            <DialogDescription>
              {t('deleteConfirm')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteConfirmDialog(false)}>
              {tCommon('cancel')}
            </Button>
            <Button onClick={handleDelete} disabled={deleteLoading} variant="destructive">
              {deleteLoading ? tCommon('loading') : tCommon('confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Copy Success Dialog */}
      <Dialog open={showCopySuccessDialog} onOpenChange={setShowCopySuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('copyLink')}</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="flex gap-2">
              <Input
                value={copiedLink}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                onClick={() => {
                  try {
                    navigator.clipboard.writeText(copiedLink);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                    toast({
                      title: t('copySuccess'),
                      description: t('copySuccessDesc'),
                    });
                  } catch (error) {
                    console.error('Copy failed:', error);
                    toast({
                      title: tCommon('error'),
                      description: t('copyFailed') || 'Failed to copy',
                      variant: 'destructive',
                    });
                  }
                }}
                variant="outline"
                size="icon"
                className="shrink-0"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-sm text-[#b3b3b3]">
              {t('copySuccessDesc')}
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowCopySuccessDialog(false)}>
              {tCommon('close')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
