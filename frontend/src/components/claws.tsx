'use client';

import { useEffect, useState, useRef, useMemo } from 'react';
import Anser from 'ansi-to-html';
import { useTranslations } from 'next-intl';
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
import { Plus, Edit, Trash2, ScrollText, FolderOpen, RotateCcw, MoreVertical, Check, CheckCircle2, X, Undo, ChevronsDown, Globe, MessageCircle } from 'lucide-react';
import { clawAPI, modelAPI, apiKeyAPI, adminAPI } from '@/lib/services';
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
  daily_tokens_used: number;
  daily_token_limit?: number;
  last_reset_date?: string;
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
function getTypeLabel(type: string, t: (key: string) => string): string {
  const labels: Record<string, string> = {
    NANOBOT: t('type.NANOBOT'),
    OPENCLAW: t('type.OPENCLAW'),
  };
  return labels[type] || type;
}

const CHAT_TOOLS = [
  { value: 'WEIXIN', label: '微信', icon: '💬', supportedTypes: ['OPENCLAW'] },
  { value: 'LARK', label: '飞书', icon: '💬', supportedTypes: ['OPENCLAW'] },
  { value: 'QQ', label: 'QQ', icon: '📱', supportedTypes: ['NANOBOT', 'OPENCLAW'] }
];

// 状态样式配置（不包含标签文本，仅样式）
const STATUS_STYLES: Record<string, string> = {
  PENDING:  'bg-[#ffa42b]/10 text-[#ffa42b] border border-[#ffa42b]/20',
  RUNNING:  'bg-green-100  text-green-700  border border-[#1ed760]/20',
  FAILED:   'bg-red-100    text-red-700    border border-[#f3727f]/20',
  STOPPED:  'bg-[#282828]   text-[#b3b3b3]   border border-[#4d4d4d]',
  UNHEALTHY: 'bg-[#ffa42b]/10 text-[#ffa42b] border border-[#ffa42b]/20',
};

// 获取状态显示配置
function getStatusConfig(status: string, t: (key: string) => string): { label: string; className: string } {
  const statusKeyMap: Record<string, string> = {
    PENDING: 'status.pending',
    RUNNING: 'status.running',
    FAILED: 'status.failed',
    STOPPED: 'status.stopped',
    UNHEALTHY: 'status.failed', // 复用失败翻译
  };
  const key = statusKeyMap[status] || 'status.failed';
  return {
    label: t(key),
    className: STATUS_STYLES[status] ?? 'bg-[#282828] text-[#b3b3b3]'
  };
}

// ANSI 转换器实例
const anser = new Anser({
  fg: '#CCC',           // 默认前景色
  bg: '#000',           // 默认背景色
  newline: true,        // 保留换行
  escapeXML: true,      // 转义 XML 特殊字符
  stream: false,
});

function StatusBadge({ status, t }: { status: string; t: (key: string) => string }) {
  const cfg = getStatusConfig(status, t);
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

// 双色胶囊图标（后悔药）
function CapsuleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="capsuleGradient" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="50%" stopColor="#4F46E5" />
          <stop offset="50%" stopColor="#E5E7EB" />
        </linearGradient>
      </defs>
      <path d="M10.5 20.5l10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="url(#capsuleGradient)" />
    </svg>
  );
}

// Step indicator for create flow
function CreateStepIndicator({ currentPhase, chatTool }: { currentPhase: 'config' | 'starting' | 'feishu' | 'weixin' | 'success'; chatTool: string }) {
  const steps = [
    { key: 'config', label: '基础配置', icon: '1' },
    { key: 'starting', label: '启动中', icon: '2' },
    ...(chatTool === 'LARK' ? [{ key: 'feishu', label: '飞书授权', icon: '3' }] : []),
    ...(chatTool === 'WEIXIN' ? [{ key: 'weixin', label: '微信授权', icon: '3' }] : []),
  ];

  const getStepStatus = (stepKey: string) => {
    const order = ['config', 'starting', 'feishu', 'weixin', 'success'];
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
                ? 'bg-[#1ed760]/10 text-[#1ed760]'
                : status === 'current'
                ? 'bg-[#1ed760] text-white'
                : 'bg-[#282828] text-[#535353]'
            }`}>
              {status === 'completed' ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <span className="w-4 h-4 flex items-center justify-center text-xs">{step.icon}</span>
              )}
              <span>{step.label}</span>
            </div>
            {!isLast && (
              <div className={`w-8 h-0.5 mx-1 ${status === 'completed' ? 'bg-green-300' : 'bg-[#282828]'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ClawsPage() {
  const t = useTranslations('claws');
  const tCommon = useTranslations('common');
  const [claws, setClaws] = useState<Claw[]>([]);
  const [loading, setLoading] = useState(true);
  const [clawCreationDisabled, setClawCreationDisabled] = useState(false);

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('OPENCLAW');
  const [newQqBotId, setNewQqBotId] = useState('');
  const [newQqBotSecret, setNewQqBotSecret] = useState('');
  const [newBrainModel, setNewBrainModel] = useState('glm-4.7');
  const [newChatTool, setNewChatTool] = useState('WEIXIN');
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

  // Weixin authorization state
  const [weixinPhase, setWeixinPhase] = useState<'idle' | 'installing' | 'done'>('idle');
  const [weixinOutput, setWeixinOutput] = useState<string[]>([]);
  const weixinAbortRef = useRef<AbortController | null>(null);
  const weixinScrollRef = useRef<HTMLDivElement | null>(null);

  // Create flow phase: 'config' -> 'starting' -> 'feishu'/'weixin' -> 'success'
  const [createPhase, setCreatePhase] = useState<'config' | 'starting' | 'feishu' | 'weixin' | 'success'>('config');

  // Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editingClaw, setEditingClaw] = useState<Claw | null>(null);
  const [editName, setEditName] = useState('');
  const [editDailyLimit, setEditDailyLimit] = useState('');
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

  // Archive dialog
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [archiveClaw, setArchiveClaw] = useState<Claw | null>(null);
  const [archives, setArchives] = useState<any[]>([]);
  const [archivesLoading, setArchivesLoading] = useState(false);
  const [creatingArchive, setCreatingArchive] = useState(false);
  const [restoringArchive, setRestoringArchive] = useState(false);
  const [deletingArchive, setDeletingArchive] = useState(false);
  const [archiveToDelete, setArchiveToDelete] = useState<string | null>(null);
  const [deleteArchiveOpen, setDeleteArchiveOpen] = useState(false);

  // Chat Tool 设置对话框状态
  const [chatToolOpen, setChatToolOpen] = useState(false);
  const [chatToolClaw, setChatToolClaw] = useState<Claw | null>(null);
  const [selectedChatTool, setSelectedChatTool] = useState<string | null>(null);
  const [chatToolOutput, setChatToolOutput] = useState<string[]>([]);
  const [chatToolSetting, setChatToolSetting] = useState(false);
  const chatToolAbortRef = useRef<AbortController | null>(null);
  const chatToolScrollRef = useRef<HTMLDivElement | null>(null);

  // Archive feature flags
  const [pruncEnabled, setPruncEnabled] = useState(false);
  const [clawsArchiveEnabled, setClawsArchiveEnabled] = useState(false);
  const [clawsArchiveAutoEnabled, setClawsArchiveAutoEnabled] = useState(false);
  const [nextBackupTime, setNextBackupTime] = useState<string | null>(null);
  // Archive pagination
  const [archivePage, setArchivePage] = useState(1);
  const ARCHIVES_PER_PAGE = 5;

  // System config for claw daily limit max value
  const [clawApikeyDailyLimit, setClawApikeyDailyLimit] = useState<number | null>(null);

  // System config for max claws per user
  const [maxClawsPerUser, setMaxClawsPerUser] = useState(10);

  const { toast } = useToast();

  const openFilebrowser = (clawId: number) => {
    const token = useAuthStore.getState().token;
    if (token) {
      document.cookie = `sharinmod-fb-token=${encodeURIComponent(token)}; path=/; SameSite=Strict`;
    }
    window.open(`/api/claws/${clawId}/filebrowser/`, '_blank');
  };

  const openOpenClawWeb = (clawId: number) => {
    const token = useAuthStore.getState().token;
    if (token) {
      document.cookie = `sharinmod-ow-token=${encodeURIComponent(token)}; path=/; SameSite=Strict`;
    }
    window.open(`/api/claws/${clawId}/openclaw-web/`, '_blank');
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

  // Auto-scroll weixin output to bottom
  useEffect(() => {
    if (weixinScrollRef.current) {
      weixinScrollRef.current.scrollTop = weixinScrollRef.current.scrollHeight;
    }
  }, [weixinOutput]);

  // Auto-scroll chat tool output to bottom
  useEffect(() => {
    if (chatToolScrollRef.current) {
      chatToolScrollRef.current.scrollTop = chatToolScrollRef.current.scrollHeight;
    }
  }, [chatToolOutput]);

  const loadClaws = async () => {
    try {
      const [clawsResult, configResult] = await Promise.allSettled([
        clawAPI.getMyClaws(),
        clawAPI.getConfig(),
      ]);
      if (clawsResult.status === 'fulfilled') {
        setClaws(clawsResult.value.data.items ?? []);
      } else {
        console.error('Failed to load claws list:', clawsResult.reason);
      }
      // 根据后端配置决定「领养龙虾」入口是否显示
      if (configResult.status === 'fulfilled') {
        setClawCreationDisabled(configResult.value.data.enable_creation === false);
      } else {
        console.error('Failed to load claw config:', configResult.reason);
      }
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

  // Load archive feature flags on mount
  useEffect(() => {
    const loadArchiveFlags = async () => {
      try {
        const configRes = await clawAPI.getConfig();
        setPruncEnabled(configRes.data.prunc_enabled ?? false);
        setClawsArchiveEnabled(configRes.data.claws_archive_enabled ?? false);
        setClawsArchiveAutoEnabled(configRes.data.claws_archive_auto_enabled ?? false);

        // Calculate next backup time for interval backups
        const intervalMinutes = configRes.data.claws_archive_schedule_interval ?? 20;
        const now = new Date();
        const nextBackup = new Date(now.getTime() + intervalMinutes * 60 * 1000);
        setNextBackupTime(nextBackup.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }));
      } catch {
        // 静默失败
      }
    };
    loadArchiveFlags();
  }, []);

  // Load system settings config for claw daily limit max value and max claws per user
  useEffect(() => {
    const loadSystemSettings = async () => {
      try {
        const configRes = await adminAPI.getSystemSettingsConfig();
        setClawApikeyDailyLimit(configRes.data.claw_apikey_daily_token_limit);
        setMaxClawsPerUser(configRes.data.max_claws_per_user);
      } catch {
        // 静默失败，使用 null 表示无限制，使用默认值 10
        setClawApikeyDailyLimit(null);
        setMaxClawsPerUser(10);
      }
    };
    loadSystemSettings();
  }, []);

  const resetCreateForm = () => {
    setNewName('');
    setNewType('OPENCLAW');
    setNewQqBotId('');
    setNewQqBotSecret('');
    setNewBrainModel('glm-4.7');
    setNewChatTool('WEIXIN');
    setPlazaModels([]);
    setConsecutiveErrors(0);
    consecutiveErrorsRef.current = 0;
    setLarkPhase('idle');
    setLarkOutput([]);
    setWeixinPhase('idle');
    setWeixinOutput([]);
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

            // OPENCLAW + LARK: enter Lark QR scan phase
            if (newType === 'OPENCLAW' && newChatTool === 'LARK') {
              setCreatePhase('feishu');
              setLarkPhase('installing');
              setLarkOutput([]);
              startLarkInstall(createdClaw.id);
            } else if (newType === 'OPENCLAW' && newChatTool === 'WEIXIN') {
              setCreatePhase('weixin');
              setWeixinPhase('installing');
              setWeixinOutput([]);
              startWeixinLogin(createdClaw.id);
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

  const startWeixinLogin = async (clawId: number) => {
    if (weixinAbortRef.current) {
      weixinAbortRef.current.abort();
    }
    const abort = new AbortController();
    weixinAbortRef.current = abort;
    const token = useAuthStore.getState().token || '';

    try {
      const resp = await clawAPI.weixinLogin(clawId, token);
      if (!resp.ok || !resp.body) {
        setWeixinOutput(prev => [...prev, `[错误] HTTP ${resp.status}`]);
        setWeixinPhase('done');
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
            setWeixinOutput(prev => [...prev.slice(-300), line]);
          }
        }
      }
      setWeixinPhase('done');
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setWeixinOutput(prev => [...prev, '[连接中断]']);
        setWeixinPhase('done');
      }
    }
  };

  const openChatToolDialog = (claw: Claw) => {
    setChatToolClaw(claw);
    setSelectedChatTool('WEIXIN');
    setChatToolOutput([]);
    setChatToolSetting(false);
    setChatToolOpen(true);
  };

  const startSetChatTool = async () => {
    if (!chatToolClaw || !selectedChatTool) return;
    if (chatToolAbortRef.current) {
      chatToolAbortRef.current.abort();
    }
    const abort = new AbortController();
    chatToolAbortRef.current = abort;
    const token = useAuthStore.getState().token || '';

    setChatToolSetting(true);
    setChatToolOutput([]);

    try {
      const resp = await clawAPI.setChatTool(chatToolClaw.id, { chat_tool: selectedChatTool! }, token);
      if (!resp.ok || !resp.body) {
        setChatToolOutput(prev => [...prev, `[错误] HTTP ${resp.status}`]);
        setChatToolSetting(false);
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
            setChatToolOutput(prev => [...prev.slice(-300), line]);
          }
        }
      }
      // 完成后刷新列表
      loadClaws();
      setChatToolSetting(false);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setChatToolOutput(prev => [...prev, '[连接中断]']);
      }
      setChatToolSetting(false);
    }
  };

  const openEdit = (claw: Claw) => {
    setEditingClaw(claw);
    setEditName(claw.name);
    setEditDailyLimit(claw.daily_token_limit?.toString() || '');
    setEditOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingClaw || !editName.trim()) {
      toast({ title: '错误', description: '名称不能为空', variant: 'destructive' });
      return;
    }

    // 验证每日限额
    let dailyLimit: number | null = null;
    const isAdmin = useAuthStore.getState().user?.is_admin;
    const minValue = isAdmin ? 0 : 1;
    // 使用系统配置的龙虾 APIKey 每日限额作为最大值，如果没有配置则使用默认值
    const maxLimit = clawApikeyDailyLimit ?? 999999999;

    if (editDailyLimit !== '') {
      // 检查是否包含小数点或逗号
      if (editDailyLimit.includes('.') || editDailyLimit.includes(',')) {
        toast({ title: '错误', description: '每日限额必须为整数', variant: 'destructive' });
        return;
      }
      // 检查科学计数法
      if (editDailyLimit.toLowerCase().includes('e')) {
        toast({ title: '错误', description: '请输入完整的数字，不要使用科学计数法', variant: 'destructive' });
        return;
      }

      const parsed = parseInt(editDailyLimit, 10);
      if (isNaN(parsed)) {
        toast({ title: '错误', description: '请输入有效的每日限额数值', variant: 'destructive' });
        return;
      }
      if (parsed < minValue) {
        const msg = isAdmin ? '每日限额不能为负数' : `每日限额不能小于 ${minValue}`;
        toast({ title: '错误', description: msg, variant: 'destructive' });
        return;
      }
      if (parsed > maxLimit) {
        const msg = clawApikeyDailyLimit
          ? `每日限额不能超过系统设定值 ${maxLimit}`
          : `每日限额不能超过 ${maxLimit}`;
        toast({ title: '错误', description: msg, variant: 'destructive' });
        return;
      }
      dailyLimit = parsed;
    }

    setSaving(true);
    try {
      // 并行执行两个 API 调用
      const updates = [];
      updates.push(clawAPI.updateClaw(editingClaw.id, { name: editName.trim() }));

      // 如果有 unified_api_key_id，同时更新限额
      if (editingClaw.unified_api_key_id) {
        updates.push(apiKeyAPI.updateUnifiedAPIKey(editingClaw.unified_api_key_id, {
          daily_token_limit: dailyLimit,
        }));
      }

      await Promise.all(updates);
      // 根据更新内容显示不同的成功提示
      const message = editingClaw.unified_api_key_id
        ? (editDailyLimit === '' ? '名称已更新，每日限额已清除' : '名称和每日限额已更新')
        : '名称已更新';
      toast({ title: '成功', description: message });
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

    // 立即更新本地状态为"重启中"（PENDING）
    setClaws(prevClaws =>
      prevClaws.map(claw =>
        claw.id === restartingClaw.id ? { ...claw, status: 'PENDING' } : claw
      )
    );

    // 关闭对话框并清除状态
    setRestartOpen(false);
    setRestartingClaw(null);

    try {
      await clawAPI.restartClaw(restartingClaw.id);
      toast({ title: '成功', description: `龙虾「${restartingClaw.name}」已开始重启` });
      // 重启成功后刷新列表获取最新状态
      loadClaws();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '重启失败，请重试',
        variant: 'destructive',
      });
      // 失败时刷新列表恢复原状态
      loadClaws();
    } finally {
      setRestarting(false);
    }
  };

  const openArchive = async (claw: Claw) => {
    setArchiveClaw(claw);
    setArchives([]);
    setArchivesLoading(true);
    setArchivePage(1); // 重置到第一页
    setArchiveOpen(true);
    try {
      const response = await clawAPI.getArchives(claw.id);
      setArchives(response.data.items ?? []);
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '获取存档列表失败',
        variant: 'destructive',
      });
    } finally {
      setArchivesLoading(false);
    }
  };

  const handleCreateArchive = async () => {
    if (!archiveClaw) return;
    setCreatingArchive(true);
    try {
      const response = await clawAPI.createArchive(archiveClaw.id);
      toast({ title: '成功', description: '存档创建成功' });
      // Reload archives
      const archivesResponse = await clawAPI.getArchives(archiveClaw.id);
      setArchives(archivesResponse.data.items ?? []);
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '创建存档失败',
        variant: 'destructive',
      });
    } finally {
      setCreatingArchive(false);
    }
  };

  const handleRestoreArchive = async (timestamp: string) => {
    if (!archiveClaw) return;
    setRestoringArchive(true);
    try {
      await clawAPI.restoreArchive(archiveClaw.id, timestamp);
      toast({ title: '成功', description: '存档恢复成功，龙虾正在重启' });
      setArchiveOpen(false);
      setArchiveClaw(null);
      loadClaws();
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '恢复存档失败',
        variant: 'destructive',
      });
    } finally {
      setRestoringArchive(false);
    }
  };

  const openDeleteArchive = (timestamp: string) => {
    setArchiveToDelete(timestamp);
    setDeleteArchiveOpen(true);
  };

  const handleDeleteArchive = async () => {
    if (!archiveClaw || !archiveToDelete) return;
    setDeletingArchive(true);
    try {
      await clawAPI.deleteArchive(archiveClaw.id, archiveToDelete);
      toast({ title: '成功', description: '存档已删除' });
      setDeleteArchiveOpen(false);
      setArchiveToDelete(null);
      // Reload archives
      const response = await clawAPI.getArchives(archiveClaw.id);
      setArchives(response.data.items ?? []);
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.detail || '删除存档失败',
        variant: 'destructive',
      });
    } finally {
      setDeletingArchive(false);
    }
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false,
    });

  const formatArchiveTime = (timestamp: string | number) => {
    const date = new Date(Number(timestamp) * 1000);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <div className="space-y-6">
      <Card className="border border-[#282828] shadow-md rounded-2xl bg-[#181818]">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xl font-bold text-white">{t('title')}</CardTitle>
            <CardDescription className="text-[#b3b3b3] mt-1">
              {t('description', { max: maxClawsPerUser })}
            </CardDescription>
          </div>
          {!clawCreationDisabled && (
            <Button
              onClick={() => setCreateOpen(true)}
              className="bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              {t('createButton')}
            </Button>
          )}
          {clawCreationDisabled && (
            <div className="text-sm text-[#535353] bg-[#282828] px-3 py-1.5 rounded-lg">
              {t('disabledMessage')}
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-[#535353] font-medium">{t('loading')}</div>
          ) : claws.length === 0 ? (
            <div className="text-center py-12 text-[#535353]">
              <div className="text-4xl mb-3">🦞</div>
              <p className="font-medium">{t('emptyState.title')}</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('table.name')}</TableHead>
                  <TableHead>{t('table.type')}</TableHead>
                  <TableHead>{t('table.chatTool')}</TableHead>
                  <TableHead>{t('table.status')}</TableHead>
                  <TableHead>{t('table.dailyLimit')}</TableHead>
                  <TableHead>{t('table.createdAt')}</TableHead>
                  <TableHead className="text-right">{t('table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {claws.map((claw) => (
                  <TableRow key={claw.id}>
                    <TableCell className="font-medium">{claw.name}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[#282828] text-[#b3b3b3] border border-[#4d4d4d]">
                        {getTypeLabel(claw.type, t)}
                      </span>
                    </TableCell>
                    <TableCell>
                      {claw.chat_tool === 'QQ' ? (
                        <img src="/icons/qq.svg" alt="QQ" className="w-5 h-5" />
                      ) : claw.chat_tool === 'LARK' ? (
                        <img src="/icons/feishu.png" alt="飞书" className="w-5 h-5" />
                      ) : claw.chat_tool === 'WEIXIN' ? (
                        <img src="/icons/weixin.png" alt="微信" className="w-5 h-5" />
                      ) : null}
                    </TableCell>
                    <TableCell><StatusBadge status={claw.status} t={t} /></TableCell>
                    <TableCell className="text-[#b3b3b3]">
                      <div className="space-y-1.5 min-w-[120px]">
                        {claw.daily_token_limit && claw.daily_token_limit > 0 ? (
                          (() => {
                            const usageRatio = Math.max(0, claw.daily_tokens_used) / claw.daily_token_limit;
                            const barWidth = Math.min(Math.max(0, usageRatio) * 100, 100);
                            const barColor = usageRatio >= 0.8 ? 'bg-red-500' : usageRatio >= 0.5 ? 'bg-amber-500' : 'bg-emerald-500';
                            return (
                              <>
                                <div className="h-1.5 bg-[#282828] rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full transition-all duration-300 ${barColor}`}
                                    style={{ width: `${barWidth}%` }}
                                  />
                                </div>
                                <div className="flex items-center gap-1">
                                  <span className="text-xs font-medium tabular-nums">
                                    {claw.daily_tokens_used.toLocaleString()}
                                  </span>
                                  <span className="text-[#535353] text-xs">/</span>
                                  <span className="text-xs text-[#535353] tabular-nums">
                                    {claw.daily_token_limit.toLocaleString()}
                                  </span>
                                </div>
                              </>
                            );
                          })()
                        ) : (
                          <>
                            <div className="h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden">
                              <div className="h-full bg-[#1ed760] rounded-full w-0" />
                            </div>
                            <div className="flex items-center gap-1">
                              <span className="text-xs font-medium tabular-nums">
                                {claw.daily_tokens_used.toLocaleString()}
                              </span>
                              <span className="text-[#535353] text-xs">/</span>
                              <span className="text-xs text-[#535353] font-mono">+inf</span>
                            </div>
                          </>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-[#b3b3b3]">{formatDate(claw.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openFilebrowser(claw.id)}
                          className="rounded-lg border-[#4d4d4d] hover:bg-[#1f1f1f] hover:border-[#4d4d4d]"
                          title={t('tooltip.filebrowser')}
                        >
                          <FolderOpen className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openOpenClawWeb(claw.id)}
                          className="rounded-lg border-[#4d4d4d] hover:bg-[#1f1f1f] hover:border-[#4d4d4d]"
                          title={t('tooltip.openclawweb')}
                        >
                          <Globe className="w-3.5 h-3.5" />
                        </Button>
                        {(pruncEnabled && clawsArchiveEnabled) && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openArchive(claw)}
                            className="rounded-lg border-[#4d4d4d] hover:bg-[#1f1f1f] hover:border-[#4d4d4d]"
                            title="后悔药"
                          >
                            <CapsuleIcon className="w-3.5 h-3.5" />
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openRestart(claw)}
                          className="rounded-lg border-[#4d4d4d] hover:bg-[#1f1f1f] hover:border-[#4d4d4d]"
                          title={t('tooltip.restart')}
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
                            <DropdownMenuItem onClick={() => openLogs(claw)}>
                              <ScrollText className="w-4 h-4 mr-2" />
                              {t('tooltip.logs')}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openEdit(claw)}>
                              <Edit className="w-4 h-4 mr-2" />
                              {t('tooltip.edit')}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => openChatToolDialog(claw)}
                              disabled={claw.type !== 'OPENCLAW' || claw.status !== 'RUNNING'}
                            >
                              <MessageCircle className="w-4 h-4 mr-2" />
                              重连
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => openDelete(claw)} className="text-red-600">
                              <Trash2 className="w-4 h-4 mr-2" />
                              {t('tooltip.delete')}
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
          weixinAbortRef.current?.abort();
          setCreatePhase('config');
          resetCreateForm();
        }
        setCreateOpen(open);
      }}>
        <DialogContent
          className="sm:max-w-lg rounded-2xl"
          onPointerDownOutside={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>
              {createPhase === 'config' && '领养龙虾 🦞'}
              {createPhase === 'starting' && '正在启动龙虾...'}
              {createPhase === 'feishu' && '飞书授权'}
              {createPhase === 'weixin' && '微信授权'}
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
                    <SelectLabel className="text-xs text-[#b3b3b3] font-semibold">✨ 主流模型</SelectLabel>
                    {featuredBrainModels.map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectGroup>
                  {plazaModels.filter((m) => !featuredBrainModels.includes(m.model_name)).length > 0 && (
                    <SelectGroup>
                      <SelectLabel className="text-xs text-[#535353] font-normal">广场中的其他模型</SelectLabel>
                      {plazaModels
                        .filter((m) => !featuredBrainModels.includes(m.model_name))
                        .map((m) => (
                          <SelectItem key={m.model_name} value={m.model_name} className="text-[#535353]">
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
              <div className="grid grid-cols-3 gap-2">
                {CHAT_TOOLS.filter(t => t.supportedTypes.includes(newType)).map((tool) => (
                  <button
                    key={tool.value}
                    type="button"
                    onClick={() => setNewChatTool(tool.value)}
                    className={`flex items-center justify-center gap-2 p-2.5 rounded-xl border-2 transition-all ${
                      newChatTool === tool.value
                        ? 'border-[#1ed760] bg-[#1f1f1f]'
                        : 'border-[#4d4d4d] hover:border-[#4d4d4d]'
                    }`}
                  >
                    {tool.value === 'QQ' ? (
                      <img src="/icons/qq.svg" alt="QQ" className="w-5 h-5" />
                    ) : tool.value === 'LARK' ? (
                      <img src="/icons/feishu.png" alt="飞书" className="w-5 h-5" />
                    ) : tool.value === 'WEIXIN' ? (
                      <img src="/icons/weixin.png" alt="微信" className="w-5 h-5" />
                    ) : null}
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
                  className="text-xs text-[#b3b3b3] hover:underline"
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
                  <div className="w-20 h-20 border-4 border-[#4d4d4d] rounded-full"></div>
                  <div className="absolute top-0 left-0 w-20 h-20 border-4 border-[#1ed760] rounded-full border-t-transparent animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl">🦞</span>
                  </div>
                </div>
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold text-white">正在启动龙虾...</h3>
                <p className="text-sm text-[#b3b3b3]">预计需要 1-2 分钟，请耐心等待</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[#b3b3b3] font-medium">启动进度</span>
                  <span className="text-[#b3b3b3]">
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
              <div className="flex items-center gap-3 p-4 bg-[#1f1f1f] border border-[#4d4d4d] rounded-xl">
                <img src="/icons/feishu.png" alt="飞书" className="w-8 h-8" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    {larkPhase === 'installing' ? '正在获取授权二维码...' : '请用飞书扫描二维码完成授权'}
                  </p>
                  <p className="text-xs text-[#b3b3b3] mt-1">推荐使用个人飞书账号</p>
                </div>
              </div>

              {larkOutput.length > 0 && (
                <div
                  ref={larkScrollRef}
                  className="max-h-96 overflow-y-auto bg-gray-950 rounded-lg p-3 w-full"
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
                  <div className="inline-block w-8 h-8 border-2 border-[#1ed760] border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm text-[#b3b3b3] mt-2">正在生成二维码...</p>
                </div>
              )}
            </div>
          )}

          {/* Phase 3: Weixin Authorization */}
          {createPhase === 'weixin' && (
            <div className="space-y-4 py-2">
              <div className="flex items-center gap-3 p-4 bg-green-50 border border-[#1ed760]/20 rounded-xl">
                <img src="/icons/weixin.png" alt="微信" className="w-8 h-8" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">
                    {weixinPhase === 'installing' ? '正在获取授权二维码...' : '请用微信扫描二维码完成授权'}
                  </p>
                  <p className="text-xs text-green-600 mt-1">推荐使用个人微信账号</p>
                </div>
              </div>

              {weixinOutput.length > 0 && (
                <div
                  ref={weixinScrollRef}
                  className="max-h-96 overflow-y-auto bg-gray-950 rounded-lg p-3 w-full"
                >
                  <div className="font-mono text-xs leading-tight text-gray-100 whitespace-pre-wrap break-all">
                    {weixinOutput.map((line, i) => (
                      <div
                        key={i}
                        dangerouslySetInnerHTML={{ __html: anser.toHtml(line) }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {weixinOutput.length === 0 && weixinPhase === 'installing' && (
                <div className="text-center py-4">
                  <div className="inline-block w-8 h-8 border-2 border-green-600 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm text-[#b3b3b3] mt-2">正在生成二维码...</p>
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
                <h3 className="text-xl font-semibold text-white">龙虾创建成功！</h3>
                <p className="text-sm text-[#b3b3b3] mt-2">龙虾「{newName}」已准备就绪</p>
              </div>
              <div className="flex items-center justify-center gap-2 text-sm text-[#b3b3b3]">
                <span className="inline-flex items-center px-2 py-1 rounded-md bg-[#282828] text-[#b3b3b3]">
                  {getTypeLabel(newType, t)}
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
                className="w-full bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl"
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
                  className="bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl"
                >
                  已完成扫码
                </Button>
              </>
            )}

            {createPhase === 'weixin' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => {
                    weixinAbortRef.current?.abort();
                    setWeixinPhase('idle');
                    setWeixinOutput([]);
                    setCreatePhase('success');
                    loadClaws();
                    toast({ title: '提示', description: '您可以稍后在设置中完成微信授权' });
                  }}
                  className="rounded-xl"
                >
                  跳过授权
                </Button>
                <Button
                  onClick={() => {
                    weixinAbortRef.current?.abort();
                    setWeixinPhase('idle');
                    setWeixinOutput([]);
                    setCreatePhase('success');
                    loadClaws();
                    toast({ title: '成功', description: '龙虾创建成功！' });
                  }}
                  className="bg-green-600 hover:bg-green-700 text-white rounded-xl"
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
                  className="bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl"
                >
                  {creating ? '创建中...' : '创建'}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={(open) => {
        if (!open) {
          setEditDailyLimit('');
        }
        setEditOpen(open);
      }}>
        <DialogContent className="sm:max-w-sm rounded-2xl">
          <DialogHeader>
            <DialogTitle>编辑龙虾</DialogTitle>
            <DialogDescription>修改龙虾「{editingClaw?.name}」的名称和每日限额</DialogDescription>
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
          <div className="space-y-1.5 py-2">
            <Label htmlFor="edit-daily-limit">{t('dailyLimitLabel')}</Label>
            <Input
              id="edit-daily-limit"
              type="number"
              min={useAuthStore.getState().user?.is_admin ? "0" : "1"}
              max={clawApikeyDailyLimit?.toString() || "999999999"}
              step="1"
              value={editDailyLimit}
              onChange={(e) => setEditDailyLimit(e.target.value)}
              className="rounded-xl"
              placeholder={t('dailyLimitPlaceholder')}
            />
            <p className="text-xs text-[#b3b3b3]">
              {clawApikeyDailyLimit
                ? t('dailyLimitHint', { max: clawApikeyDailyLimit })
                : t('unlimited')}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)} className="rounded-xl">取消</Button>
            <Button
              onClick={handleSaveEdit}
              disabled={saving}
              className="bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl"
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
              className="bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl"
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
              <ScrollText className="w-4 h-4 text-[#b3b3b3]" />
              龙虾「{logsClawName}」实时日志
              {logsLoading && <span className="text-xs font-normal text-[#535353]">连接中...</span>}
              <button
                onClick={() => setLogsAutoFollow((v) => !v)}
                className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-md transition-colors ${
                  logsAutoFollow
                    ? 'bg-[#1ed760] text-white'
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
                    <div className="w-12 flex-shrink-0 text-right text-[#b3b3b3] text-xs select-none pl-2 pr-[2px] leading-5">
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

      {/* Archive Dialog */}
      <Dialog open={archiveOpen} onOpenChange={(open) => { if (!open) { setArchiveOpen(false); setArchiveClaw(null); } else { setArchiveOpen(open); } }}>
        <DialogContent className="sm:max-w-2xl rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CapsuleIcon className="w-4 h-4" />
              龙虾「{archiveClaw?.name}」后悔药
            </DialogTitle>
            <DialogDescription>
              管理龙虾的数据快照，随时回滚到历史状态
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Header row with create button and next backup time */}
            <div className="flex items-center justify-between gap-4">
              {clawsArchiveAutoEnabled && nextBackupTime ? (
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-xl">
                  <span className="text-blue-600">🕐</span>
                  <p className="text-xs text-blue-700">
                    下次自动备份: <span className="font-medium">{nextBackupTime}</span>
                  </p>
                </div>
              ) : (
                <div></div>
              )}
              <Button
                onClick={handleCreateArchive}
                disabled={creatingArchive || archiveClaw?.status !== 'RUNNING'}
                className="bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl flex-shrink-0"
              >
                {creatingArchive ? '创建中...' : '创建存档'}
              </Button>
            </div>

            {/* Archives List */}
            {archivesLoading ? (
              <div className="text-center py-8 text-[#535353] font-medium">加载中...</div>
            ) : archives.length === 0 ? (
              <div className="text-center py-12 text-[#535353]">
                <div className="text-3xl mb-2">💾</div>
                <p className="text-sm">暂无存档</p>
              </div>
            ) : (
              <>
                <div className="border border-[#4d4d4d] rounded-xl overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-[#1f1f1f]">
                        <TableHead className="w-48">版本时间</TableHead>
                        <TableHead className="w-20 text-center">类型</TableHead>
                        <TableHead className="w-24 text-center">是否可用</TableHead>
                        <TableHead className="text-right w-40">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {archives
                        .slice((archivePage - 1) * ARCHIVES_PER_PAGE, archivePage * ARCHIVES_PER_PAGE)
                        .map((archive, idx) => (
                          <TableRow key={archive.timestamp || idx}>
                            <TableCell className="font-mono text-sm">
                              {formatArchiveTime(archive.timestamp)}
                            </TableCell>
                            <TableCell className="text-center">
                              {archive.auto_created === true ? (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-100 text-blue-700 border border-blue-200 text-xs">
                                  自动
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#282828] text-[#b3b3b3] border border-[#4d4d4d] text-xs">
                                  手动
                                </span>
                              )}
                            </TableCell>
                            <TableCell className="text-center">
                              {archive.ready_to_use === true ? (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#1ed760]/10 text-[#1ed760] border border-[#1ed760]/20 text-xs">
                                  可用
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#ffa42b]/10 text-[#ffa42b] border border-[#ffa42b]/20 text-xs">
                                  准备中
                                </span>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleRestoreArchive(archive.timestamp)}
                                  disabled={restoringArchive || !archive.ready_to_use}
                                  className="hover:bg-[#1f1f1f] text-[#b3b3b3]"
                                  title="恢复存档"
                                >
                                  <Undo className="w-3.5 h-3.5" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openDeleteArchive(archive.timestamp)}
                                  disabled={deletingArchive || !archive.ready_to_use}
                                  className="hover:bg-red-50 text-red-600"
                                  title="删除存档"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Pagination */}
                {archives.length > ARCHIVES_PER_PAGE && (
                  <div className="flex items-center justify-between px-4 py-3 bg-[#1f1f1f] border-t border-[#4d4d4d]">
                    <span className="text-sm text-[#b3b3b3]">
                      第 {archivePage} / {Math.ceil(archives.length / ARCHIVES_PER_PAGE)} 页
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setArchivePage(p => Math.max(1, p - 1))}
                        disabled={archivePage === 1}
                        className="rounded-lg"
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setArchivePage(p => Math.min(Math.ceil(archives.length / ARCHIVES_PER_PAGE), p + 1))}
                        disabled={archivePage === Math.ceil(archives.length / ARCHIVES_PER_PAGE)}
                        className="rounded-lg"
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <DialogFooter />
        </DialogContent>
      </Dialog>

      {/* Delete Archive Confirmation Dialog */}
      <Dialog open={deleteArchiveOpen} onOpenChange={setDeleteArchiveOpen}>
        <DialogContent className="sm:max-w-sm rounded-2xl">
          <DialogHeader>
            <DialogTitle>删除存档</DialogTitle>
            <DialogDescription>
              确定要删除存档吗？删除后将无法恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setDeleteArchiveOpen(false); setArchiveToDelete(null); }} className="rounded-xl">取消</Button>
            <Button
              onClick={handleDeleteArchive}
              disabled={deletingArchive}
              variant="destructive"
              className="rounded-xl"
            >
              {deletingArchive ? '删除中...' : '确认删除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ChatTool Dialog */}
      <Dialog open={chatToolOpen} onOpenChange={(open) => {
        if (!open) {
          chatToolAbortRef.current?.abort();
          setChatToolOutput([]);
        }
        setChatToolOpen(open);
      }}>
        <DialogContent className="sm:max-w-lg rounded-2xl">
          <DialogHeader>
            <DialogTitle>重连对话工具</DialogTitle>
            <DialogDescription>
              为龙虾「{chatToolClaw?.name}」重新连接对话工具
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* 对话工具选择按钮 */}
            <div className="grid grid-cols-3 gap-2">
              {CHAT_TOOLS.filter(t => t.supportedTypes.includes('OPENCLAW') && t.value !== 'QQ').map((tool) => (
                <button
                  key={tool.value}
                  type="button"
                  disabled={chatToolSetting}
                  onClick={() => setSelectedChatTool(tool.value)}
                  className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 transition-all cursor-pointer ${
                    selectedChatTool === tool.value
                      ? 'border-[#1ed760] bg-[#1f1f1f]'
                      : 'border-[#4d4d4d] hover:border-[#4d4d4d]'
                  } ${chatToolSetting ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {tool.value === 'LARK' ? (
                    <img src="/icons/feishu.png" alt="飞书" className="w-5 h-5" />
                  ) : tool.value === 'WEIXIN' ? (
                    <img src="/icons/weixin.png" alt="微信" className="w-5 h-5" />
                  ) : null}
                  <span className="text-sm font-medium">{tool.label}</span>
                </button>
              ))}
              {/* QQ - 灰掉 */}
              <button
                disabled
                className="flex items-center justify-center gap-2 p-3 rounded-xl border-2 border-[#282828] bg-[#1f1f1f] opacity-50 cursor-not-allowed"
                title="暂不支持"
              >
                <img src="/icons/qq.svg" alt="QQ" className="w-5 h-5 grayscale" />
                <span className="text-sm font-medium text-[#535353]">QQ</span>
              </button>
            </div>

            {/* 确认按钮 */}
            {selectedChatTool && !chatToolSetting && (
              <Button
                onClick={startSetChatTool}
                className="w-full bg-[#1ed760] hover:bg-[#1ed760]/90 text-white rounded-xl cursor-pointer"
              >
                确认切换到 {CHAT_TOOLS.find(t => t.value === selectedChatTool)?.label}
              </Button>
            )}

            {/* 命令输出区域 */}
            {(chatToolOutput.length > 0 || chatToolSetting) && (
              <div
                ref={chatToolScrollRef}
                className="max-h-96 overflow-y-auto bg-gray-950 rounded-lg p-3 w-full"
              >
                {chatToolSetting && chatToolOutput.length === 0 && (
                  <div className="text-xs text-[#535353]">正在重连对话工具...</div>
                )}
                <div className="font-mono text-xs leading-tight text-gray-100 whitespace-pre-wrap break-all">
                  {chatToolOutput.map((line, i) => (
                    <div
                      key={i}
                      dangerouslySetInnerHTML={{ __html: anser.toHtml(line) }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                chatToolAbortRef.current?.abort();
                setChatToolOpen(false);
              }}
              disabled={chatToolSetting}
              className="rounded-xl"
            >
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
