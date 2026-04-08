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

function formatTokens(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return n.toLocaleString();
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN', {
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
        title: '加载失败',
        description: error.response?.data?.detail || '无法加载成员列表',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [currentOrganization, toast]);

  const handleDisable = async () => {
    if (!targetMember || !currentOrganization) return;
    setActionLoading(true);
    try {
      await organizationAPI.disableMember(currentOrganization.id, targetMember.user_id);
      setMembers(prev => prev.map(m =>
        m.user_id === targetMember.user_id ? { ...m, is_disabled: true } : m
      ));
      toast({ title: '成功', description: `已禁用成员 ${targetMember.email}` });
    } catch (error: any) {
      toast({
        title: '操作失败',
        description: error.response?.data?.detail || '禁用失败',
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
      toast({ title: '成功', description: `已启用成员 ${targetMember.email}` });
    } catch (error: any) {
      toast({
        title: '操作失败',
        description: error.response?.data?.detail || '启用失败',
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
      toast({ title: '成功', description: `已移除成员 ${targetMember.email}` });
    } catch (error: any) {
      toast({
        title: '操作失败',
        description: error.response?.data?.detail || '移除失败',
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
        title: '生成失败',
        description: error.response?.data?.detail || '无法生成邀请链接',
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
    toast({ title: '链接已复制', description: '邀请链接已复制到剪贴板' });
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isAuthenticated || !currentOrganization || myOrganizations === null) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-600" />
            我的团队
          </h1>
          <p className="text-sm text-gray-500 mt-1">{currentOrganization.name}</p>
        </div>
        <Button
          onClick={handleCreateInvite}
          disabled={inviteLoading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4" />
          邀请用户
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-gray-700">
            成员列表（{members.length} 人）
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">加载中...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>邮箱</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>总使用</TableHead>
                  <TableHead>最近使用</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.user_id} className={member.is_disabled ? 'opacity-60' : ''}>
                    <TableCell>
                      <div>
                        <div className="font-medium text-sm">{member.email}</div>
                        {member.name && <div className="text-xs text-gray-400">{member.name}</div>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        member.role === 'owner'
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {member.role === 'owner' ? '创建者' : '成员'}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatTokens(member.org_total_tokens)} tokens
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {formatDate(member.last_used_at)}
                    </TableCell>
                    <TableCell>
                      {member.is_disabled && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-600 font-medium">
                          已禁用
                        </span>
                      )}
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
                              启用
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs gap-1 text-amber-600 border-amber-200 hover:bg-amber-50"
                              onClick={() => { setTargetMember(member); setShowDisableDialog(true); }}
                            >
                              <Ban className="w-3.5 h-3.5" />
                              禁用
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs gap-1 text-red-600 border-red-200 hover:bg-red-50"
                            onClick={() => { setTargetMember(member); setShowRemoveDialog(true); }}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            移除
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {members.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-gray-400 py-8">
                      暂无成员，点击「邀请用户」添加第一个成员
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
            <DialogTitle>确认禁用成员</DialogTitle>
            <DialogDescription>
              确定要禁用成员 <strong>{targetMember?.email}</strong> 吗？禁用后该成员状态将标记为已禁用。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDisableDialog(false)} disabled={actionLoading}>取消</Button>
            <Button variant="destructive" onClick={handleDisable} disabled={actionLoading}>
              {actionLoading ? '处理中...' : '确认禁用'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Enable confirmation */}
      <Dialog open={showEnableDialog} onOpenChange={setShowEnableDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认启用成员</DialogTitle>
            <DialogDescription>
              确定要启用成员 <strong>{targetMember?.email}</strong> 吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEnableDialog(false)} disabled={actionLoading}>取消</Button>
            <Button onClick={handleEnable} disabled={actionLoading} className="bg-green-600 hover:bg-green-700">
              {actionLoading ? '处理中...' : '确认启用'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove confirmation */}
      <Dialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认移除成员</DialogTitle>
            <DialogDescription>
              确定要从私服中移除成员 <strong>{targetMember?.email}</strong> 吗？此操作不可撤销，但不影响该用户的平台账号。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRemoveDialog(false)} disabled={actionLoading}>取消</Button>
            <Button variant="destructive" onClick={handleRemove} disabled={actionLoading}>
              {actionLoading ? '处理中...' : '确认移除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Invite dialog */}
      <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>邀请用户加入私服</DialogTitle>
            <DialogDescription>
              将以下链接发送给受邀用户，对方登录后点击链接即可加入私服。
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
                {copied ? '已复制' : '复制'}
              </Button>
            </div>
            <p className="text-xs text-gray-400">邀请链接有效期 7 天，仅可使用一次。</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInviteDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
