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
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/toast';
import { Plus, Edit, Trash2, ScrollText, ChevronsDown, FolderOpen, RotateCcw, MoreVertical, Check, CheckCircle2, X } from 'lucide-react';
import { clawAPI, modelAPI } from '@/lib/services';
import { useAuthStore } from '@/lib/store';

interface Claw {
  id: number;
  name: string;
  type: string;
  qq_bot_id: string;
  k8s_deployment_name?: string;
  status: string;
  ready?: boolean;
  created_at: string;
  updated_at: string;
  brain_model?: string;
  chat_tool?: string;
  unified_api_key_id?: number;
  user_id?: number;
}

const CLAW_TYPES = [
  { value: 'NANOBOT', label: '性能型 (NanoBot)' },
  { value: 'OPENCLAW', label: '全能型 (OpenClaw)' },
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
};

const CHAT_TOOLS = [
  { value: 'QQ', label: 'QQ', icon: '📱', supportedTypes: ['NANOBOT', 'OPENCLAW'] },
  { value: 'FEISHU', label: '飞书', icon: '💬', supportedTypes: ['OPENCLAW'] }
];

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PENDING:  { label: '准备中', className: 'bg-yellow-100 text-yellow-700 border border-yellow-200' },
  RUNNING:  { label: '运行中', className: 'bg-green-100  text-green-700  border border-green-200' },
  FAILED:   { label: '失败',   className: 'bg-red-100    text-red-700    border border-red-200' },
  STOPPED:  { label: '已停止', className: 'bg-gray-100   text-gray-700   border border-gray-200' },
  UNHEALTHY: { label: '不健康', className: 'bg-orange-100 text-orange-700 border border-orange-200' },
};

// 获取状态显示配置
function getStatusConfig(status: string): { label: string; className: string } {
  // 对未知状态返回安全的默认值，避免暴露内部状态字符串
  return STATUS_LABELS[status] ?? { label: '未知状态', className: 'bg-gray-100 text-gray-700' };
}

// ANSI 转换器实例
const anser = new Anser({
  fg: '#CCC',           // 默认前景色
  bg: '#000',           // 默认背景色
  newline: true,        // 保留换行
  escapeXML: true,      // 转义 XML 特殊字符
  stream: false,
});

function StatusBadge({ status }: { status: string }) {
  const cfg = getStatusConfig(status);
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

// Step indicator for create flow
function CreateStepIndicator({ currentPhase, chatTool }: { currentPhase: 'config' | 'starting' | 'feishu' | 'success'; chatTool: string }) {
  const steps = [
    { key: 'config', label: '基础配置', icon: '1' },
    { key: 'starting', label: '启动中', icon: '2' },
    ...(chatTool === 'FEISHU' ? [{ key: 'feishu', label: '飞书授权', icon: '3' }] : []),
  ];

  const getStepStatus = (stepKey: string) => {
    const order = ['config', 'starting', 'feishu', 'success'];
    const currentIndex = order.indexOf(currentPhase);
    const stepIndex = order.indexOf(stepKey);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  };

  return (
    <div className="flex items-center justify-center gap-2 py-2">
      {steps.map((step, index) => {
        const status = getStepStatus(step.key);
        const isLast = index === steps.length - 1;

        return (
          <div key={step.key} className="flex items-center">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
              status === 'completed'
                ? 'bg-green-100 text-green-700'
                : status === 'current'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-400'
            }`}>
              {status === 'completed' ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <span className="w-4 h-4 flex items-center justify-center text-xs">{step.icon}</span>
              )}
              <span>{step.label}</span>
            </div>
            {!isLast && (
              <div className={`w-8 h-0.5 mx-1 ${status === 'completed' ? 'bg-green-300' : 'bg-gray-200'}`} />
            )}
          </div>
        );
      })}
    </div>
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
  const [newChatTool, setNewChatTool] = useState('QQ');
  const [plazaModels, setPlazaModels] = useState<PlazaModel[]>([]);
  const [featuredBrainModels, setFeaturedBrainModels] = useState<string[]>(DEFAULT_FEATURED_BRAIN_MODELS);
  const [loadingBrainModels, setLoadingBrainModels] = useState(false);

  // Polling state for claw creation progress
  const [pollingClawId, setPollingClawId] = useState<number | null>(null);
  const [consecutiveErrors, setConsecutiveErrors] = useState<number>(0);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef<number>(0);
  const pollingStartTimeRef = useRef<number>(0);

  // Feishu QR scan phase state
  const [larkPhase, setLarkPhase] = useState<'idle' | 'installing' | 'done'>('idle');
  const [larkOutput, setLarkOutput] = useState<string[]>([]);
  const larkAbortRef = useRef<AbortController | null>(null);
  const larkScrollRef = useRef<HTMLDivElement | null>(null);

  // Create flow phase: 'config' -> 'starting' -> 'feishu' -> 'success'
  const [createPhase, setCreatePhase] = useState<'config' | 'starting' | 'feishu' | 'success'>('config');

  // Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editingClaw, setEditingClaw] = useState<Claw | null>(null);
  const [editName, setEditName] = useState('');
  const [saving, setSaving] = useState(false);

  // Delete dialog
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingClaw, setDeletingClaw] = useState<Claw | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Restart dialog
  const [restartOpen, setRestartOpen] = useState(false);
  const [restartingClaw, setRestartingClaw] = useState<Claw | null>(null);
  const [restarting, setRestarting] = useState(false);

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

  // Auto-scroll lark output to bottom
  useEffect(() => {
    if (larkScrollRef.current) {
      larkScrollRef.current.scrollTop = larkScrollRef.current.scrollHeight;
    }
  }, [larkOutput]);

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

  // Cleanup polling timer on unmount
  useEffect(() => {
    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
    };
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
    setNewChatTool('QQ');
    setPlazaModels([]);
    setConsecutiveErrors(0);
    consecutiveErrorsRef.current = 0;
    setLarkPhase('idle');
    setLarkOutput([]);
    setCreatePhase('config');
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

    if (!newName.trim() || !newBrainModel.trim()) {
      toast({ title: '错误', description: '请填写所有必填字段', variant: 'destructive' });
      return;
    }
    if (newChatTool === 'QQ' && (!newQqBotId.trim() || !newQqBotSecret.trim())) {
      toast({ title: '错误', description: '请填写 AppID 和 AppSecret', variant: 'destructive' });
      return;
    }
    setCreating(true);
    setCreatePhase('starting');
    try {
      const response = await clawAPI.createClaw({
        name: newName.trim(),
        type: newType,
        qq_bot_id: newChatTool === 'QQ' ? newQqBotId.trim() : '',
        qq_bot_secret: newChatTool === 'QQ' ? newQqBotSecret.trim() : '',
        brain_model: newBrainModel,
        chat_tool: newChatTool,
      });
      const createdClaw = response.data;

      // Start polling for status
      setPollingClawId(createdClaw.id);
      pollingStartTimeRef.current = Date.now();
      setConsecutiveErrors(0);
      consecutiveErrorsRef.current = 0;

      const MAX_CONSECUTIVE_ERRORS = 10;

      // Poll every 2 seconds
      pollingTimerRef.current = setInterval(async () => {
        try {
          const pollResponse = await clawAPI.getClaw(createdClaw.id);
          const claw = pollResponse.data;

          // Reset error count on success
          consecutiveErrorsRef.current = 0;
          setConsecutiveErrors(0);

          if (claw.status === 'PENDING') {
            // 继续等待（包括 ContainerCreating 等正常情况）
            // 不做任何操作，继续轮询
          } else if (claw.status === 'RUNNING') {
            // RUNNING 即视为成功
            if (pollingTimerRef.current) {
              clearInterval(pollingTimerRef.current);
              pollingTimerRef.current = null;
            }
            setPollingClawId(null);
            setCreating(false);

            // OPENCLAW + FEISHU: enter Lark QR scan phase
            if (newType === 'OPENCLAW' && newChatTool === 'FEISHU') {
              setCreatePhase('feishu');
              setLarkPhase('installing');
              setLarkOutput([]);
              startLarkInstall(createdClaw.id);
            } else {
              setCreatePhase('success');
              loadClaws();
            }
          } else if (claw.status === 'FAILED') {
            // Failed
            if (pollingTimerRef.current) {
              clearInterval(pollingTimerRef.current);
              pollingTimerRef.current = null;
            }
            setPollingClawId(null);
            setCreating(false);
            setCreatePhase('config');
            loadClaws();
            toast({
              title: '创建失败',
              description: '龙虾启动失败，请查看日志了解详情',
              variant: 'destructive',
            });
          } else if (Date.now() - pollingStartTimeRef.current > 5 * 60 * 1000) {
            // Timeout after 5 minutes
            if (pollingTimerRef.current) {
              clearInterval(pollingTimerRef.current);
              pollingTimerRef.current = null;
            }
            setPollingClawId(null);
            setCreating(false);
            setCreatePhase('config');
            loadClaws();
            toast({
              title: '创建超时',
              description: '龙虾启动超时，请稍后检查状态',
              variant: 'destructive',
            });
          }
        } catch (error) {
          consecutiveErrorsRef.current += 1;
          setConsecutiveErrors(consecutiveErrorsRef.current);
          console.error('Polling error:', error);

          // Stop polling after too many consecutive errors
          if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS) {
            if (pollingTimerRef.current) {
              clearInterval(pollingTimerRef.current);
              pollingTimerRef.current = null;
            }
            setPollingClawId(null);
            setCreating(false);
            setCreatePhase('config');
            loadClaws();
            toast({
              title: '连接失败',
              description: '无法获取龙虾状态，请稍后检查状态',
              variant: 'destructive',
            });
          }
        }
      }, 2000);

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
      setCreating(false);
      setCreatePhase('config');
    }
  };

  // Stop polling when dialog closes
  const stopPolling = () => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
    setPollingClawId(null);
    setCreating(false);
  };

  const startLarkInstall = async (clawId: number) => {
    if (larkAbortRef.current) {
      larkAbortRef.current.abort();
    }
    const abort = new AbortController();
    larkAbortRef.current = abort;
    const token = useAuthStore.getState().token || '';

    try {
      const resp = await clawAPI.larkInstall(clawId, token);
      if (!resp.ok || !resp.body) {
        setLarkOutput(prev => [...prev, `[错误] HTTP ${resp.status}`]);
        setLarkPhase('done');
        return;
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';
        for (const part of parts) {
          if (part.startsWith('data: ')) {
            const line = part.slice(6);
            setLarkOutput(prev => [...prev.slice(-300), line]);
          }
        }
      }
      setLarkPhase('done');
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setLarkOutput(prev => [...prev, '[连接中断]']);
        setLarkPhase('done');
      }
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

  const openRestart = (claw: Claw) => {
    setRestartingClaw(claw);
    setRestartOpen(true);
  };

  const handleRestart = async () => {
    if (!restartingClaw) return;
    setRestarting(true);
    try {
      await clawAPI.restartClaw(restartingClaw.id);
      toast({ title: '成功', description: `龙虾「${restartingClaw.name}」重启成功` });
      setRestartOpen(false);
      setRestartingClaw(null);
      loadClaws();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '重启失败，请重试',
        variant: 'destructive',
      });
    } finally {
      setRestarting(false);
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
                    <TableCell>
                      {claw.chat_tool === 'QQ' ? (
                        <img src="/icons/qq.svg" alt="QQ" className="w-5 h-5" />
                      ) : (
                        <img src="/icons/feishu.png" alt="飞书" className="w-5 h-5" />
                      )}
                    </TableCell>
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
                          onClick={() => openRestart(claw)}
                          className="rounded-lg border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300"
                          title="重启"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm" className="rounded-lg">
                              <MoreVertical className="w-3.5 h-3.5" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEdit(claw)}>
                              <Edit className="w-4 h-4 mr-2" />
                              编辑
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => openDelete(claw)} className="text-red-600">
                              <Trash2 className="w-4 h-4 mr-2" />
                              删除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
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
      <Dialog open={createOpen} onOpenChange={(open) => {
        if (!open) {
          stopPolling();
          larkAbortRef.current?.abort();
          setCreatePhase('config');
          resetCreateForm();
        }
        setCreateOpen(open);
      }}>
        <DialogContent className="sm:max-w-lg rounded-2xl">
          <DialogHeader>
            <DialogTitle>
              {createPhase === 'config' && '领养龙虾 🦞'}
              {createPhase === 'starting' && '正在启动龙虾...'}
              {createPhase === 'feishu' && '飞书授权'}
              {createPhase === 'success' && '创建成功！'}
            </DialogTitle>
            {createPhase !== 'config' && (
              <CreateStepIndicator currentPhase={createPhase} chatTool={newChatTool} />
            )}
          </DialogHeader>

          {/* Phase 1: Configuration Form */}
          {createPhase === 'config' && (
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
              <Select value={newType} onValueChange={(v) => {
                setNewType(v);
                // 重置对话工具为第一个可用选项
                const tools = CHAT_TOOLS.filter(t => t.supportedTypes.includes(v));
                if (tools.length > 0) setNewChatTool(tools[0].value);
              }}>
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
              <Label>对话工具 <span className="text-red-500">*</span></Label>
              <div className="grid grid-cols-2 gap-3">
                {CHAT_TOOLS.filter(t => t.supportedTypes.includes(newType)).map((tool) => (
                  <button
                    key={tool.value}
                    type="button"
                    onClick={() => setNewChatTool(tool.value)}
                    className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 transition-all ${
                      newChatTool === tool.value
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300'
                    }`}
                  >
                    {tool.value === 'QQ' ? (
                      <img src="/icons/qq.svg" alt="QQ" className="w-5 h-5" />
                    ) : (
                      <img src="/icons/feishu.png" alt="飞书" className="w-5 h-5" />
                    )}
                    <span className="text-sm font-medium">{tool.label}</span>
                  </button>
                ))}
              </div>
            </div>
            {newChatTool === 'QQ' && (
            <>
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
            </>
            )}
          </div>
          )}

          {/* Phase 2: Starting Progress */}
          {createPhase === 'starting' && (
            <div className="py-8 space-y-4">
              <div className="flex justify-center">
                <div className="relative">
                  <div className="w-20 h-20 border-4 border-indigo-200 rounded-full"></div>
                  <div className="absolute top-0 left-0 w-20 h-20 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl">🦞</span>
                  </div>
                </div>
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold text-gray-900">正在启动龙虾...</h3>
                <p className="text-sm text-gray-500">预计需要 1-2 分钟，请耐心等待</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-indigo-700 font-medium">启动进度</span>
                  <span className="text-gray-500">
                    {Math.min((Date.now() - pollingStartTimeRef.current) / 1000 / 60 * 100 / 5, 100).toFixed(0)}%
                  </span>
                </div>
                <Progress value={Math.min((Date.now() - pollingStartTimeRef.current) / 1000 / 60 * 100 / 5, 100)} className="h-2" />
              </div>
            </div>
          )}

          {/* Phase 3: Feishu Authorization */}
          {createPhase === 'feishu' && (
            <div className="space-y-4 py-2">
              <div className="flex items-center gap-3 p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
                <img src="/icons/feishu.png" alt="飞书" className="w-8 h-8" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-indigo-900">
                    {larkPhase === 'installing' ? '正在获取授权二维码...' : '请用飞书扫描二维码完成授权'}
                  </p>
                  <p className="text-xs text-indigo-600 mt-1">推荐使用个人飞书账号</p>
                </div>
              </div>

              {larkOutput.length > 0 && (
                <div
                  ref={larkScrollRef}
                  className="max-h-72 overflow-y-auto bg-gray-950 rounded-lg p-3 w-full"
                >
                  <div className="font-mono text-xs leading-tight text-gray-100 whitespace-pre-wrap break-all">
                    {larkOutput.map((line, i) => (
                      <div
                        key={i}
                        dangerouslySetInnerHTML={{ __html: anser.toHtml(line) }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {larkOutput.length === 0 && larkPhase === 'installing' && (
                <div className="text-center py-4">
                  <div className="inline-block w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm text-gray-500 mt-2">正在生成二维码...</p>
                </div>
              )}
            </div>
          )}

          {/* Phase 4: Success */}
          {createPhase === 'success' && (
            <div className="py-8 text-center space-y-4">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full">
                <Check className="w-10 h-10 text-green-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">龙虾创建成功！</h3>
                <p className="text-sm text-gray-500 mt-2">龙虾「{newName}」已准备就绪</p>
              </div>
              <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
                <span className="inline-flex items-center px-2 py-1 rounded-md bg-indigo-100 text-indigo-700">
                  {TYPE_DISPLAY_NAMES[newType] || newType}
                </span>
                <span>•</span>
                <span>{newBrainModel}</span>
              </div>
            </div>
          )}
          <DialogFooter>
            {createPhase === 'success' && (
              <Button
                onClick={() => {
                  setCreateOpen(false);
                  resetCreateForm();
                  loadClaws();
                  toast({ title: '成功', description: '龙虾创建成功！' });
                }}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl"
              >
                完成
              </Button>
            )}

            {createPhase === 'feishu' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => {
                    larkAbortRef.current?.abort();
                    setLarkPhase('idle');
                    setLarkOutput([]);
                    setCreatePhase('success');
                    loadClaws();
                    toast({ title: '提示', description: '您可以稍后在设置中完成飞书授权' });
                  }}
                  className="rounded-xl"
                >
                  跳过授权
                </Button>
                <Button
                  onClick={() => {
                    larkAbortRef.current?.abort();
                    setLarkPhase('idle');
                    setLarkOutput([]);
                    setCreatePhase('success');
                    loadClaws();
                    toast({ title: '成功', description: '龙虾创建成功！' });
                  }}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl"
                >
                  已完成扫码
                </Button>
              </>
            )}

            {createPhase === 'config' && (
              <>
                <Button variant="outline" onClick={() => { stopPolling(); setCreateOpen(false); }} className="rounded-xl">
                  取消
                </Button>
                <Button
                  onClick={handleCreate}
                  disabled={creating}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl"
                >
                  {creating ? '创建中...' : '创建'}
                </Button>
              </>
            )}
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

      {/* Restart Confirmation Dialog */}
      <Dialog open={restartOpen} onOpenChange={setRestartOpen}>
        <DialogContent className="sm:max-w-sm rounded-2xl">
          <DialogHeader>
            <DialogTitle>重启龙虾 🔄</DialogTitle>
            <DialogDescription>
              确定要重启龙虾「{restartingClaw?.name}」吗？重启后龙虾将重新连接。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRestartOpen(false)} className="rounded-xl">取消</Button>
            <Button
              onClick={handleRestart}
              disabled={restarting}
              className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl"
            >
              {restarting ? '重启中...' : '确认重启'}
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