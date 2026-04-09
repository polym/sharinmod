'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Ban, Power, Trash2, Users, Plus, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { organizationAPI } from '@/lib/services';
import { useToast } from '@/components/ui/toast';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';

interface OrgMemberStats {
  user_id: number;
  email: string;
  name?: string;
  role: string;
  is_disabled: boolean;
  org_total_tokens: number;
  last_used_at: string | null;
  joined_at: string;
}

function formatTokens(tokens: number): string {
  if (tokens < 1000) {
    return tokens.toLocaleString();
  } else if (tokens < 1000000) {
    return (tokens / 1000).toFixed(1) + 'K';
  } else if (tokens < 1000000000) {
    return (tokens / 1000000).toFixed(1) + 'M';
  } else {
    return (tokens / 1000000000).toFixed(1) + 'B';
  }
}

function formatDate(dateStr: string | null, locale: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export default function MyTeamPage() {
  const router = useRouter();
  const { currentOrganization, myOrganizations, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const { locale } = useLocaleStore();
  const t = useTranslations('myTeam');
  const tCommon = useTranslations('common');
  const { toast } = useToast();

  const [members, setMembers] = useState<OrgMemberStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Disable confirmation dialog
  const [showDisableDialog, setShowDisableDialog] = useState(false);
  const [showEnableDialog, setShowEnableDialog] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [targetMember, setTargetMember] = useState<OrgMemberStats | null>(null);

  // Invite dialog
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const isOrgOwner = !!currentOrganization && (myOrganizations?.owned.some(o => o.id === currentOrganization.id) ?? false);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }
    // B-1: myOrganizations is null until OrganizationSwitcher hydrates the store.
    // Wait for it before deciding to redirect, to avoid bouncing org owners on refresh.
    if (myOrganizations === null) {
      return;
    }
    if (!currentOrganization || !isOrgOwner) {
      router.push('/overview');
      return;
    }
    loadMembers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentOrganization, isAuthenticated, isOrgOwner, myOrganizations]);

  const loadMembers = useCallback(async () => {
    if (!currentOrganization) return;
    setLoading(true);
    try {
      const response = await organizationAPI.listMembers(currentOrganization.id);
      setMembers(response.data.items);
    } catch (error: any) {
      toast({
        title: t('toast.loadFailed'),
        description: error.response?.data?.detail || t('toast.loadFailedDetail'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [currentOrganization, toast, t]);

  const handleDisable = async () => {
    if (!targetMember || !currentOrganization) return;
    setActionLoading(true);
    try {
      await organizationAPI.disableMember(currentOrganization.id, targetMember.user_id);
      setMembers(prev => prev.map(m =>
        m.user_id === targetMember.user_id ? { ...m, is_disabled: true } : m
      ));
      toast({ title: t('toast.success'), description: t('toast.disableSuccess', { email: targetMember.email }) });
    } catch (error: any) {
      toast({
        title: t('toast.actionFailed'),
        description: error.response?.data?.detail || t('toast.disableFailed'),
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
      setShowDisableDialog(false);
      setTargetMember(null);
    }
  };

  const handleEnable = async () => {
    if (!targetMember || !currentOrganization) return;
    setActionLoading(true);
    try {
      await organizationAPI.enableMember(currentOrganization.id, targetMember.user_id);
      setMembers(prev => prev.map(m =>
        m.user_id === targetMember.user_id ? { ...m, is_disabled: false } : m
      ));
      toast({ title: t('toast.success'), description: t('toast.enableSuccess', { email: targetMember.email }) });
    } catch (error: any) {
      toast({
        title: t('toast.actionFailed'),
        description: error.response?.data?.detail || t('toast.enableFailed'),
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
      setShowEnableDialog(false);
      setTargetMember(null);
    }
  };

  const handleRemove = async () => {
    if (!targetMember || !currentOrganization) return;
    setActionLoading(true);
    try {
      await organizationAPI.removeMember(currentOrganization.id, targetMember.user_id);
      setMembers(prev => prev.filter(m => m.user_id !== targetMember.user_id));
      toast({ title: t('toast.success'), description: t('toast.removeSuccess', { email: targetMember.email }) });
    } catch (error: any) {
      toast({
        title: t('toast.actionFailed'),
        description: error.response?.data?.detail || t('toast.removeFailed'),
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
      setShowRemoveDialog(false);
      setTargetMember(null);
    }
  };

  const handleCreateInvite = async () => {
    if (!currentOrganization) return;
    setInviteLoading(true);
    setInviteToken(null);
    try {
      const response = await organizationAPI.createInvite(currentOrganization.id);
      setInviteToken(response.data.token);
      setShowInviteDialog(true);
    } catch (error: any) {
      toast({
        title: t('toast.generateFailed'),
        description: error.response?.data?.detail || t('toast.generateFailedDetail'),
        variant: 'destructive',
      });
    } finally {
      setInviteLoading(false);
    }
  };

  const inviteUrl = inviteToken
    ? (typeof window !== 'undefined' ? `${window.location.origin}/invite/${inviteToken}` : `/invite/${inviteToken}`)
    : '';

  const handleCopyInvite = async () => {
    if (!inviteUrl) return;
    await navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    toast({ title: t('toast.linkCopied'), description: t('toast.linkCopiedHint') });
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isAuthenticated || !currentOrganization || myOrganizations === null) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-gray-500">{tCommon('loading')}</div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-600" />
            {t('title')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">{currentOrganization.name}</p>
        </div>
        <Button
          onClick={handleCreateInvite}
          disabled={inviteLoading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4" />
          {t('inviteUser')}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-gray-700">
            {t('memberList', { count: members.length })}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">{tCommon('loading')}</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('email')}</TableHead>
                  <TableHead>{t('roleLabel')}</TableHead>
                  <TableHead>{t('totalUsage')}</TableHead>
                  <TableHead>{t('lastUsed')}</TableHead>
                  <TableHead className="text-right">{t('actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.user_id} className={member.is_disabled ? 'opacity-60' : ''}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium flex items-center gap-1.5">
                          {member.email}
                          {member.role === 'owner' && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 flex-shrink-0">
                              {t('role.owner')}
                            </span>
                          )}
                          {member.is_disabled && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-500 text-white flex-shrink-0">
                              {t('statusDisabled')}
                            </span>
                          )}
                        </span>
                        {member.name && (
                          <span className="text-xs text-gray-500">{member.name}</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {member.role === 'owner' ? t('role.owner') : t('role.member')}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatTokens(member.org_total_tokens)}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {formatDate(member.last_used_at, locale)}
                    </TableCell>
                    <TableCell className="text-right">
                      {member.role !== 'owner' && (
                        <div className="flex items-center justify-end gap-2">
                          {member.is_disabled ? (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs gap-1 text-green-600 border-green-200 hover:bg-green-50"
                              onClick={() => { setTargetMember(member); setShowEnableDialog(true); }}
                            >
                              <Power className="w-3.5 h-3.5" />
                              {t('enableMember')}
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs gap-1 text-amber-600 border-amber-200 hover:bg-amber-50"
                              onClick={() => { setTargetMember(member); setShowDisableDialog(true); }}
                            >
                              <Ban className="w-3.5 h-3.5" />
                              {t('disableMember')}
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs gap-1 text-red-600 border-red-200 hover:bg-red-50"
                            onClick={() => { setTargetMember(member); setShowRemoveDialog(true); }}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            {t('removeMember')}
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {members.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-gray-400 py-8">
                      {t('noMembers')}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Disable confirmation */}
      <Dialog open={showDisableDialog} onOpenChange={setShowDisableDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('confirmDisableTitle')}</DialogTitle>
            <DialogDescription>
              {t('confirmDisable', { email: targetMember?.email })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDisableDialog(false)} disabled={actionLoading}>{tCommon('cancel')}</Button>
            <Button variant="destructive" onClick={handleDisable} disabled={actionLoading}>
              {actionLoading ? tCommon('loading') : tCommon('confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Enable confirmation */}
      <Dialog open={showEnableDialog} onOpenChange={setShowEnableDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('confirmEnableTitle')}</DialogTitle>
            <DialogDescription>
              {t('confirmEnable', { email: targetMember?.email })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEnableDialog(false)} disabled={actionLoading}>{tCommon('cancel')}</Button>
            <Button onClick={handleEnable} disabled={actionLoading} className="bg-green-600 hover:bg-green-700">
              {actionLoading ? tCommon('loading') : tCommon('confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove confirmation */}
      <Dialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('confirmRemoveTitle')}</DialogTitle>
            <DialogDescription>
              {t('confirmRemove', { email: targetMember?.email })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRemoveDialog(false)} disabled={actionLoading}>{tCommon('cancel')}</Button>
            <Button variant="destructive" onClick={handleRemove} disabled={actionLoading}>
              {actionLoading ? tCommon('loading') : tCommon('confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Invite dialog */}
      <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('inviteDialog.title')}</DialogTitle>
            <DialogDescription>
              {t('inviteDialog.description')}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center gap-2 bg-gray-50 rounded-lg p-3 border">
              <span className="text-sm text-gray-700 flex-1 break-all select-all">{inviteUrl}</span>
              <Button
                variant="outline"
                size="sm"
                className="shrink-0 gap-1"
                onClick={handleCopyInvite}
              >
                {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                {copied ? t('inviteDialog.copied') : t('inviteDialog.copy')}
              </Button>
            </div>
            <p className="text-xs text-gray-400">{t('inviteDialog.hint')}</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInviteDialog(false)}>{t('inviteDialog.close')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
