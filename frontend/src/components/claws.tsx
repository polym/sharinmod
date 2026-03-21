'use client';

import { useEffect, useState, useRef, useMemo } from 'react';
import Anser from 'ansi-to-html';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { Plus, Edit, Trash2, ScrollText, ChevronsDown, FolderOpen } from 'lucide-react';
import { clawAPI, modelAPI } from '@/lib/services';
import { useAuthStore } from '@/lib/store';

interface Claw {
  id: number;
  name: string;
  type: string;
  qq_bot_id: string;
  k8s_deployment_name?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

const CLAW_TYPES = [
  { value: 'NANOBOT', label: '性能型 (NanoBot)' },
  { value: 'OPENCLAW', label: '全能型 (OpenClaw)' },
  { value: 'ZEROBOT', label: '安享型 (ZeroClaw)' },
];

// 龙虾大脑 featured 模型降级默认列表（后端配置加载失败时使用）
const DEFAULT_FEATURED_BRAIN_MODELS = ['glm-4.7', 'minimax-m2.5', 'kimi-k2.5'];

interface PlazaModel {
  model_name: string;
  display_name: string;
}

// 类型显示名称映射（用于列表显示）
const TYPE_DISPLAY_NAMES: Record<string, string> = {
  NANOBOT: '性能型',
  OPENCLAW: '全能型',
  ZEROBOT: '安享型',
};

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PENDING:  { label: '准备中', className: 'bg-yellow-100 text-yellow-700 border border-yellow-200' },
  RUNNING:  { label: '运行中', className: 'bg-green-100  text-green-700  border border-green-200' },
  FAILED:   { label: '失败',   className: 'bg-red-100    text-red-700    border border-red-200' },
  STOPPED:  { label: '已停止', className: 'bg-gray-100   text-gray-700   border border-gray-200' },
};

// ANSI 转换器实例
const anser = new Anser({
  fg: '#CCC',           // 默认前景色
  bg: '#000',           // 默认背景色
  newline: true,        // 保留换行
  escapeXML: true,      // 转义 XML 特殊字符
  stream: false,
});

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_LABELS[status] ?? { label: status, className: 'bg-gray-100 text-gray-700' };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

export function ClawsPage() {
  const [claws, setClaws] = useState<Claw[]>([]);
  const [loading, setLoading] = useState(true);
  const [clawCreationDisabled, setClawCreationDisabled] = useState(false);

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('NANOBOT');
  const [newQqBotId, setNewQqBotId] = useState('');
  const [newQqBotSecret, setNewQqBotSecret] = useState('');
  const [newBrainModel, setNewBrainModel] = useState('glm-4.7');
  const [plazaModels, setPlazaModels] = useState<PlazaModel[]>([]);
  const [featuredBrainModels, setFeaturedBrainModels] = useState<string[]>(DEFAULT_FEATURED_BRAIN_MODELS);
  const [loadingBrainModels, setLoadingBrainModels] = useState(false);

  // Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editingClaw, setEditingClaw] = useState<Claw | null>(null);
  const [editName, setEditName] = useState('');
  const [saving, setSaving] = useState(false);

  // Delete dialog
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingClaw, setDeletingClaw] = useState<Claw | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Logs dialog
  const [logsOpen, setLogsOpen] = useState(false);
  const [logsClawName, setLogsClawName] = useState('');
  const [logLines, setLogLines] = useState<string[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsAutoFollow, setLogsAutoFollow] = useState(true);
  const logsAbortRef = useRef<AbortController | null>(null);
  const logsScrollRef = useRef<HTMLDivElement | null>(null);

  const { toast } = useToast();

  const openFilebrowser = (clawId: number) => {
    const token = useAuthStore.getState().token;
    if (token) {
      document.cookie = `sharinmod-fb-token=${encodeURIComponent(token)}; path=/; SameSite=Strict`;
    }
    window.open(`/api/claws/${clawId}/filebrowser/`, '_blank');
  };

  // Auto-scroll to bottom when new log lines arrive
  useEffect(() => {
    if (logsAutoFollow && logsScrollRef.current) {
      logsScrollRef.current.scrollTop = logsScrollRef.current.scrollHeight;
    }
  }, [logLines, logsAutoFollow]);

  const loadClaws = async () => {
    try {
      const response = await clawAPI.getMyClaws();
      setClaws(response.data.items ?? []);
      setClawCreationDisabled(false);
    } catch (error: any) {
      console.error('Failed to load claws:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClaws();
  }, []);

  useEffect(() => {
    if (!createOpen) return;
    const load = async () => {
      setLoadingBrainModels(true);
      try {
        const [configRes, modelsRes] = await Promise.all([
          clawAPI.getConfig(),
          modelAPI.getModels(),
        ]);
        const featured: string[] = configRes.data.featured_brain_models ?? DEFAULT_FEATURED_BRAIN_MODELS;
        const plaza: PlazaModel[] = modelsRes.data.items ?? [];
        const plazaNames = new Set(plaza.map((m: PlazaModel) => m.model_name));
        // 过滤掉广场中不可用的 featured 模型
        const availableFeatured = featured.filter((m) => plazaNames.has(m));
        setFeaturedBrainModels(availableFeatured.length > 0 ? availableFeatured : featured);
        setPlazaModels(plaza);
        // 默认选中第一个可用 featured
        const firstFeatured = availableFeatured[0] ?? featured[0];
        setNewBrainModel((prev) => prev === 'glm-4.7' ? firstFeatured : prev);
      } catch {
        // 静默失败，使用默认值
      } finally {
        setLoadingBrainModels(false);
      }
    };
    load();
  }, [createOpen]);

  const resetCreateForm = () => {
    setNewName('');
    setNewType('NANOBOT');
    setNewQqBotId('');
    setNewQqBotSecret('');
    setNewBrainModel('glm-4.7');
    setPlazaModels([]);
  };

  const handleCreate = async () => {
    // 双重检查：如果功能被禁用，直接返回
    if (clawCreationDisabled) {
      toast({
        title: '功能已禁用',
        description: '龙虾创建功能已被管理员禁用',
        variant: 'destructive',
      });
      return;
    }

    if (!newName.trim() || !newQqBotId.trim() || !newQqBotSecret.trim()) {
      toast({ title: '错误', description: '请填写所有必填字段', variant: 'destructive' });
      return;
    }
    setCreating(true);
    try {
      await clawAPI.createClaw({
        name: newName.trim(),
        type: newType,
        qq_bot_id: newQqBotId.trim(),
        qq_bot_secret: newQqBotSecret.trim(),
        brain_model: newBrainModel,
      });
      toast({ title: '成功', description: '龙虾创建成功！' });
      setCreateOpen(false);
      resetCreateForm();
      loadClaws();
    } catch (error: any) {
      // 检测功能禁用错误
      if (error.response?.status === 403) {
        setClawCreationDisabled(true);
        toast({
          title: '功能已禁用',
          description: '龙虾创建功能已被管理员禁用',
          variant: 'destructive',
        });
      } else {
        toast({
          title: '错误',
          description: error.response?.data?.detail || '创建失败，请重试',
          variant: 'destructive',
        });
      }
    } finally {
      setCreating(false);
    }
  };

  const openEdit = (claw: Claw) => {
    setEditingClaw(claw);
    setEditName(claw.name);
    setEditOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingClaw || !editName.trim()) {
      toast({ title: '错误', description: '名称不能为空', variant: 'destructive' });
      return;
    }
    setSaving(true);
    try {
      await clawAPI.updateClaw(editingClaw.id, { name: editName.trim() });
      toast({ title: '成功', description: '名称已更新' });
      setEditOpen(false);
      setEditingClaw(null);
      loadClaws();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '更新失败，请重试',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const openDelete = (claw: Claw) => {
    setDeletingClaw(claw);
    setDeleteOpen(true);
  };

  const openLogs = async (claw: Claw) => {
    if (logsAbortRef.current) {
      logsAbortRef.current.abort();
    }
    setLogsClawName(claw.name);
    setLogLines([]);
    setLogsLoading(true);
    setLogsAutoFollow(true);
    setLogsOpen(true);

    const abort = new AbortController();
    logsAbortRef.current = abort;

    while (!abort.signal.aborted) {
      try {
        const token = useAuthStore.getState().token || '';
        const resp = await fetch(`/api/claws/${claw.id}/logs`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: abort.signal,
        });
        if (!resp.ok || !resp.body) {
          setLogLines((prev) => [...prev, `[错误] 无法获取日志: HTTP ${resp.status}`]);
          setLogsLoading(false);
          break;
        }
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        setLogsLoading(false);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() ?? '';
          for (const part of parts) {
            if (part.startsWith('data: ')) {
              const line = part.slice(6);
              setLogLines((prev) => [...prev.slice(-500), line]);
            }
          }
        }
        // Stream ended cleanly (pod exited)
        if (!abort.signal.aborted) {
          setLogLines((prev) => [...prev, '--- [日志流已结束] ---']);
        }
        break;
      } catch (err: any) {
        if (err.name === 'AbortError') break;
        setLogLines((prev) => [...prev, `[连接中断，3 秒后自动重连...]`]);
        setLogsLoading(true);
        await new Promise<void>((r) => {
          const timer = setTimeout(r, 3000);
          abort.signal.addEventListener('abort', () => { clearTimeout(timer); r(); }, { once: true });
        });
      }
    }
    setLogsLoading(false);
  };

  const closeLogs = () => {
    if (logsAbortRef.current) {
      logsAbortRef.current.abort();
      logsAbortRef.current = null;
    }
    setLogsOpen(false);
    setLogLines([]);
  };

  const handleDelete = async () => {
    if (!deletingClaw) return;
    setDeleting(true);
    try {
      await clawAPI.deleteClaw(deletingClaw.id);
      toast({ title: '成功', description: `龙虾「${deletingClaw.name}」已销毁` });
      setDeleteOpen(false);
      setDeletingClaw(null);
      loadClaws();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '删除失败，请重试',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false,
    });

  return (
    <div className="space-y-6">
      <Card className="border-[3px] border-indigo-100 shadow-md rounded-2xl bg-gradient-to-br from-white to-indigo-50/30">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xl font-bold text-gray-900">领养龙虾</CardTitle>
            <CardDescription className="text-gray-500 mt-1">
              管理您的龙虾家族（最多 10 只）
            </CardDescription>
          </div>
          {!clawCreationDisabled && (
            <Button
              onClick={() => setCreateOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              创建龙虾
            </Button>
          )}
          {clawCreationDisabled && (
            <div className="text-sm text-gray-400 bg-gray-100 px-3 py-1.5 rounded-lg">
              龙虾创建功能已禁用
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-indigo-400 font-medium">加载中...</div>
          ) : claws.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <div className="text-4xl mb-3">🦞</div>
              <p className="font-medium">还没有龙虾，快去领养一只吧！</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>机器人</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {claws.map((claw) => (
                  <TableRow key={claw.id}>
                    <TableCell className="font-medium">{claw.name}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 border border-indigo-200">
                        {TYPE_DISPLAY_NAMES[claw.type] || claw.type}
                      </span>
                    </TableCell>
                    <TableCell className="font-mono text-sm text-gray-600">{claw.qq_bot_id}</TableCell>
                    <TableCell><StatusBadge status={claw.status} /></TableCell>
                    <TableCell className="text-sm text-gray-500">{formatDate(claw.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openLogs(claw)}
                          className="rounded-lg border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300"
                          title="查看日志"
                        >
                          <ScrollText className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openFilebrowser(claw.id)}
                          className="rounded-lg border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300"
                          title="文件管理"
                        >
                          <FolderOpen className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEdit(claw)}
                          className="rounded-lg border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openDelete(claw)}
                          className="rounded-lg border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) resetCreateForm(); }}>
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle>领养龙虾 🦞</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="create-name">龙虾名称 <span className="text-red-500">*</span></Label>
              <Input
                id="create-name"
                placeholder="给你的龙虾起个名字"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="rounded-xl"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="create-type">类型 <span className="text-red-500">*</span></Label>
              <Select value={newType} onValueChange={setNewType}>
                <SelectTrigger id="create-type" className="rounded-xl">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CLAW_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="create-brain-model">
                龙虾大脑🧠 <span className="text-red-500">*</span>
              </Label>
              <Select value={newBrainModel} onValueChange={setNewBrainModel}>
                <SelectTrigger id="create-brain-model" className="rounded-xl">
                  <SelectValue placeholder={loadingBrainModels ? '加载中...' : '选择模型'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel className="text-xs text-indigo-600 font-semibold">✨ 主流模型</SelectLabel>
                    {featuredBrainModels.map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectGroup>
                  {plazaModels.filter((m) => !featuredBrainModels.includes(m.model_name)).length > 0 && (
                    <SelectGroup>
                      <SelectLabel className="text-xs text-gray-400 font-normal">广场中的其他模型</SelectLabel>
                      {plazaModels
                        .filter((m) => !featuredBrainModels.includes(m.model_name))
                        .map((m) => (
                          <SelectItem key={m.model_name} value={m.model_name} className="text-gray-400">
                            {m.display_name || m.model_name}
                          </SelectItem>
                        ))}
                    </SelectGroup>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Label htmlFor="create-bot-id">AppID <span className="text-red-500">*</span></Label>
                <a
                  href="https://q.qq.com/qqbot/openclaw/login.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-500 hover:underline"
                >
                  获取 ID 和 Secret
                </a>
              </div>
              <Input
                id="create-bot-id"
                placeholder="AppID"
                value={newQqBotId}
                onChange={(e) => setNewQqBotId(e.target.value)}
                className="rounded-xl"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="create-bot-secret">AppSecret <span className="text-red-500">*</span></Label>
              <Input
                id="create-bot-secret"
                type="password"
                placeholder="AppSecret"
                value={newQqBotSecret}
                onChange={(e) => setNewQqBotSecret(e.target.value)}
                className="rounded-xl"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)} className="rounded-xl">取消</Button>
            <Button
              onClick={handleCreate}
              disabled={creating}
              className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl"
            >
              {creating ? '创建中...' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-sm rounded-2xl">
          <DialogHeader>
            <DialogTitle>修改名称</DialogTitle>
            <DialogDescription>修改龙虾「{editingClaw?.name}」的名称</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5 py-2">
            <Label htmlFor="edit-name">新名称</Label>
            <Input
              id="edit-name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="rounded-xl"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)} className="rounded-xl">取消</Button>
            <Button
              onClick={handleSaveEdit}
              disabled={saving}
              className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl"
            >
              {saving ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="sm:max-w-sm rounded-2xl">
          <DialogHeader>
            <DialogTitle>销毁龙虾</DialogTitle>
            <DialogDescription>
              确定要销毁龙虾「{deletingClaw?.name}」吗？销毁后将无法恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)} className="rounded-xl">取消</Button>
            <Button
              onClick={handleDelete}
              disabled={deleting}
              variant="destructive"
              className="rounded-xl"
            >
              {deleting ? '销毁中...' : '确认销毁'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Logs Dialog */}
      <Dialog open={logsOpen} onOpenChange={(open) => { if (!open) closeLogs(); }}>
        <DialogContent className="sm:max-w-5xl rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ScrollText className="w-4 h-4 text-indigo-500" />
              龙虾「{logsClawName}」实时日志
              {logsLoading && <span className="text-xs font-normal text-indigo-400">连接中...</span>}
              <button
                onClick={() => setLogsAutoFollow((v) => !v)}
                className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-md transition-colors ${
                  logsAutoFollow
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <ChevronsDown className="w-3 h-3" />
                自动跟随
              </button>
            </DialogTitle>
          </DialogHeader>
          <div
            ref={logsScrollRef}
            className="h-[42rem] w-full rounded-xl bg-gray-950 overflow-y-auto"
          >
            {logLines.length === 0 && !logsLoading ? (
              <div className="p-3 text-xs text-gray-100 font-mono">暂无日志...</div>
            ) : (
              <div className="font-mono text-xs flex flex-col">
                {logLines.map((line, idx) => (
                  <div key={`line-${idx}`} className="flex">
                    {/* 行号 */}
                    <div className="w-12 flex-shrink-0 text-right text-gray-500 text-xs select-none pl-2 pr-[2px] leading-5">
                      {idx + 1}
                    </div>
                    {/* 日志内容 */}
                    <div
                      className="flex-1 text-gray-100 px-3 leading-5 whitespace-pre-wrap break-all"
                      dangerouslySetInnerHTML={{ __html: anser.toHtml(line) }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}