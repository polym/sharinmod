'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/components/ui/toast';
import { Copy, Edit, Trash2, Check } from 'lucide-react';
import { apiKeyAPI, adminAPI } from '@/lib/services';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';
import { useAuthStore } from '@/lib/store';

interface UnifiedAPIKey {
  id: number;
  api_key_name: string;
  description?: string;
  api_key: string;
  status: string;
  litellm_key?: string;
  created_at: string;
  revoked_at?: string;
  last_used_at?: string;
  daily_token_limit?: number;
  daily_tokens_used: number;
  last_reset_date?: string;
}

export function UnifiedAPIKeys() {
  const t = useTranslations('apiKeys');
  const tButtons = useTranslations('apiKeys.buttons');
  const tToast = useTranslations('apiKeys.toast');
  const tCommon = useTranslations('common');
  const { locale } = useLocaleStore();
  const { user, currentOrganization } = useAuthStore();
  const orgId = currentOrganization?.id;

  const [apiKeys, setAPIKeys] = useState<UnifiedAPIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [editingKey, setEditingKey] = useState<UnifiedAPIKey | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editEnabled, setEditEnabled] = useState(true);
  const [editDailyLimit, setEditDailyLimit] = useState('');
  const [defaultDailyTokenLimit, setDefaultDailyTokenLimit] = useState<number | null>(null);
  const [loadingKeys, setLoadingKeys] = useState<Set<number>>(new Set());
  const [copiedKeyId, setCopiedKeyId] = useState<number | null>(null);
  const { toast } = useToast();

  const loadAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMyUnifiedAPIKeys(orgId);
      setAPIKeys(response.data.items);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAPIKeys();
  }, [orgId]);

  useEffect(() => {
    const loadSystemSettings = async () => {
      try {
        const configRes = await adminAPI.getSystemSettingsConfig();
        setDefaultDailyTokenLimit(configRes.data.default_daily_token_limit);
      } catch {
        setDefaultDailyTokenLimit(null);
      }
    };
    loadSystemSettings();
  }, []);

  const handleCreateUnifiedAPIKey = async () => {
    if (!name) {
      toast({
        title: tToast('error'),
        description: tToast('enterName'),
        variant: 'destructive',
      });
      return;
    }

    try {
      await apiKeyAPI.createUnifiedAPIKey({
        api_key_name: name,
        description,
        api_key_ids: [],
      }, orgId);

      toast({
        title: tToast('success'),
        description: tToast('createSuccess'),
      });

      setCreateDialogOpen(false);
      setName('');
      setDescription('');
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('createFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleBlockUnifiedAPIKey = async (id: number) => {
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.blockUnifiedAPIKey(id);
      toast({
        title: tToast('success'),
        description: tToast('blockSuccess'),
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('blockFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleEditAPIKey = (apiKey: UnifiedAPIKey) => {
    setEditingKey(apiKey);
    setEditName(apiKey.api_key_name || '');
    setEditDescription(apiKey.description || '');
    setEditEnabled(apiKey.status === 'active');
    setEditDailyLimit(apiKey.daily_token_limit?.toString() || '');
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingKey) return;

    if (!editName) {
      toast({
        title: tToast('error'),
        description: tToast('enterName'),
        variant: 'destructive',
      });
      return;
    }

    if (editingKey.status === 'active' && !editEnabled) {
      if (!confirm(tToast('confirmDisable'))) {
        return;
      }
    }

    // F6: Client-side validation for daily limit
    let dailyLimit: number | null = null;
    if (editDailyLimit !== '') {
      const parsed = parseInt(editDailyLimit, 10);
      if (isNaN(parsed)) {
        toast({
          title: tToast('error'),
          description: tToast('dailyLimitInvalid') || 'Please enter a valid number for daily limit',
          variant: 'destructive',
        });
        return;
      }
      if (parsed < 0) {
        toast({
          title: tToast('error'),
          description: tToast('dailyLimitNegative') || 'Daily limit cannot be negative',
          variant: 'destructive',
        });
        return;
      }
      dailyLimit = parsed;
    }

    try {
      await apiKeyAPI.updateUnifiedAPIKey(editingKey.id, {
        api_key_name: editName,
        description: editDescription,
        status: editEnabled ? 'active' : 'revoked',
        daily_token_limit: dailyLimit,
      });

      toast({
        title: tToast('success'),
        description: tToast('updateSuccess'),
      });

      setEditDialogOpen(false);
      setEditingKey(null);
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('updateFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleCopyAPIKey = async (key: string, id: number) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(key);
        setCopiedKeyId(id);
        setTimeout(() => setCopiedKeyId(null), 1500);
        return;
      }
    } catch (err) {
      console.warn('Clipboard API failed, trying fallback:', err);
    }

    fallbackCopy(key, id);
  };

  const fallbackCopy = (text: string, id: number) => {
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.top = '0';
      textArea.style.left = '0';
      textArea.style.width = '2em';
      textArea.style.height = '2em';
      textArea.style.padding = '0';
      textArea.style.border = 'none';
      textArea.style.outline = 'none';
      textArea.style.boxShadow = 'none';
      textArea.style.background = 'transparent';
      textArea.style.opacity = '0';

      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      try {
        textArea.setSelectionRange(0, textArea.value.length);
      } catch (e) {
        console.warn('setSelectionRange not supported:', e);
      }

      const success = document.execCommand('copy');
      document.body.removeChild(textArea);

      if (success) {
        setCopiedKeyId(id);
        setTimeout(() => setCopiedKeyId(null), 1500);
      } else {
        toast({
          title: tToast('error'),
          description: tToast('copyFailed'),
          variant: 'destructive',
        });
      }
    } catch (err) {
      console.error('Fallback copy error:', err);
      toast({
        title: tToast('error'),
        description: tToast('copyFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleUnblockUnifiedAPIKey = async (id: number) => {
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.unblockUnifiedAPIKey(id);
      toast({
        title: tToast('success'),
        description: tToast('unblockSuccess'),
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('unblockFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleDeleteUnifiedAPIKey = async (id: number) => {
    if (!confirm(tToast('confirmDelete'))) return;
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      const apiKey = apiKeys.find(k => k.id === id);
      if (apiKey?.status === 'active') {
        await apiKeyAPI.blockUnifiedAPIKey(id);
      }
      await apiKeyAPI.deleteUnifiedAPIKey(id);
      toast({
        title: tToast('success'),
        description: tToast('deleteSuccess'),
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('deleteFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleRegenerateAPIKey = async (id: number) => {
    setLoadingKeys(prev => new Set(prev).add(id));
    try {
      await apiKeyAPI.regenerateUnifiedAPIKey(id);
      toast({
        title: tToast('success'),
        description: tToast('regenerateSuccess'),
      });
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('regenerateFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoadingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const formatDate = (dateString: string) => {
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

  return (
    <div className="space-y-6">
      <Card className=" border border-[#282828] bg-[#181818]">
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <CardTitle>{t('title')}</CardTitle>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="default">
                  {t('create')}
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[560px] border border-[#282828] rounded-2xl">
                <DialogHeader className="pb-2">
                  <DialogTitle className="text-xl font-bold text-white">{t('create')}</DialogTitle>
                </DialogHeader>
                <div className="grid gap-5 py-5 px-1">
                  {/* Name Field */}
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-[#b3b3b3] font-medium text-sm">
                      {t('name')}
                    </Label>
                    <Input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className=" border border-[#282828] h-10"
                      placeholder={t('namePlaceholder')}
                    />
                  </div>

                  {/* Description Field */}
                  <div className="space-y-2">
                    <Label htmlFor="description" className="text-[#b3b3b3] font-medium text-sm">
                      {t('description')}
                    </Label>
                    <Textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className=" border border-[#282828] resize-none"
                      placeholder={t('descriptionPlaceholder')}
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter className="pt-2">
                  <Button onClick={handleCreateUnifiedAPIKey} className="">
                    {tButtons('create')}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-[#b3b3b3] font-medium">{tCommon('loading')}</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-[#b3b3b3] font-medium">
              {t('noKeys')}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="border border-[#282828]">
                <TableHeader className="bg-[#282828]">
                  <TableRow>
                    <TableHead className="text-white font-bold">{t('name')}</TableHead>
                    <TableHead className="text-white font-bold">API Key</TableHead>
                    <TableHead className="text-white font-bold">{t('status')}</TableHead>
                    <TableHead className="text-white font-bold">{t('dailyUsage')}</TableHead>
                    <TableHead className="text-white font-bold">{t('createdAt')}</TableHead>
                    <TableHead className="text-white font-bold">{t('lastUsedAt')}</TableHead>
                    <TableHead className="text-white font-bold">{t('actions')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apiKeys.map((apiKey) => (
                    <TableRow key={apiKey.id} className="hover:bg-[#1f1f1f]/50">
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-semibold text-white">{apiKey.api_key_name || t('unnamed')}</span>
                          {apiKey.description && (
                            <span
                              className="text-xs text-[#535353] line-clamp-2 break-words"
                              title={apiKey.description}
                            >
                              {apiKey.description}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {apiKey.litellm_key ? (
                            <>
                              <span className="font-mono bg-[#282828] px-2 py-1 rounded-lg text-sm text-white border border-[#4d4d4d]/50">
                                {apiKey.litellm_key.length > 10
                                  ? `${apiKey.litellm_key.substring(0, 6)}***${apiKey.litellm_key.substring(apiKey.litellm_key.length - 4)}`
                                  : apiKey.litellm_key}
                              </span>
                              <div className="flex items-center w-[92px]">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCopyAPIKey(apiKey.litellm_key!, apiKey.id)}
                                  aria-label={t('copied')}
                                  className="h-7 w-7 p-0 rounded-xl bg-[#282828] hover:bg-[#282828] text-[#b3b3b3]"
                                >
                                  {copiedKeyId === apiKey.id ? (
                                    <Check className="h-3.5 w-3.5" />
                                  ) : (
                                    <Copy className="h-3.5 w-3.5" />
                                  )}
                                </Button>
                                {copiedKeyId === apiKey.id && (
                                  <span className="text-xs text-[#b3b3b3] ml-1 inline-block w-16 font-medium">
                                    {t('copied')}
                                  </span>
                                )}
                              </div>
                            </>
                          ) : (
                            <span className="text-[#535353]">{t('noKey')}</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="min-w-[80px]">
                        {apiKey.status === 'daily_limit_exceeded' ? (
                          <span className="-warning">{t('statusDailyLimitExceeded')}</span>
                        ) : (
                          <span className={` ${apiKey.status === 'active' ? '' : ''}`}>
                            {apiKey.status === 'active' ? t('statusActive') : t('statusRevoked')}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-[#b3b3b3]">
                        <div className="space-y-1.5 min-w-[120px]">
                          {apiKey.daily_token_limit ? (
                            <>
                              <div className="h-1.5 bg-[#282828] rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-300 ${
                                    apiKey.daily_tokens_used / apiKey.daily_token_limit >= 0.8
                                      ? 'bg-red-500'
                                      : apiKey.daily_tokens_used / apiKey.daily_token_limit >= 0.5
                                      ? 'bg-amber-500'
                                      : 'bg-emerald-500'
                                  }`}
                                  style={{
                                    width: `${Math.min((apiKey.daily_tokens_used / apiKey.daily_token_limit) * 100, 100)}%`
                                  }}
                                />
                              </div>
                              <div className="flex items-center gap-1">
                                <span className="text-xs font-medium tabular-nums">
                                  {apiKey.daily_tokens_used.toLocaleString()}
                                </span>
                                <span className="text-[#535353] text-xs">/</span>
                                <span className="text-xs text-[#535353] tabular-nums">
                                  {apiKey.daily_token_limit.toLocaleString()}
                                </span>
                                {apiKey.status === 'daily_limit_exceeded' && (
                                  <span className="text-xs font-medium text-red-600" title={t('dailyLimitExceededMessage')}>
                                    ⚠
                                  </span>
                                )}
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden">
                                <div className="h-full bg-[#1ed760] rounded-full w-0" />
                              </div>
                              <div className="flex items-center gap-1">
                                <span className="text-xs font-medium tabular-nums">
                                  {apiKey.daily_tokens_used.toLocaleString()}
                                </span>
                                <span className="text-[#535353] text-xs">/</span>
                                <span className="text-xs text-[#535353] font-mono">+inf</span>
                              </div>
                            </>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-[#b3b3b3]">
                        {formatDate(apiKey.created_at)}
                      </TableCell>
                      <TableCell className="text-[#b3b3b3]">
                        {apiKey.last_used_at
                          ? formatDate(apiKey.last_used_at)
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditAPIKey(apiKey)}
                            aria-label={t('edit')}
                            disabled={loadingKeys.has(apiKey.id)}
                            className="h-8 w-8 p-0 rounded-xl bg-[#282828] hover:bg-[#282828] text-[#b3b3b3]"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUnifiedAPIKey(apiKey.id)}
                            aria-label={tCommon('delete')}
                            disabled={loadingKeys.has(apiKey.id)}
                            className="h-8 w-8 p-0 rounded-xl bg-red-100 hover:bg-red-200 text-red-600"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={(open) => {
        setEditDialogOpen(open);
        // F5: Reset edit state when dialog closes
        if (!open) {
          setEditingKey(null);
          setEditName('');
          setEditDescription('');
          setEditEnabled(true);
          setEditDailyLimit('');
        }
      }}>
        <DialogContent className="sm:max-w-[560px] border border-[#282828] rounded-2xl">
          <DialogHeader className="pb-2">
            <DialogTitle className="text-xl font-bold text-white">{t('edit')}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-5 py-5 px-1">
            {/* Name Field */}
            <div className="space-y-2">
              <Label htmlFor="edit-name" className="text-[#b3b3b3] font-medium text-sm">
                {t('name')}
              </Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className=" border border-[#282828] h-10"
                placeholder={t('namePlaceholder')}
              />
            </div>

            {/* Description Field */}
            <div className="space-y-2">
              <Label htmlFor="edit-description" className="text-[#b3b3b3] font-medium text-sm">
                {t('description')}
              </Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className=" border border-[#282828] resize-none"
                placeholder={t('optionalDescription')}
                rows={3}
              />
            </div>

            {/* Status Field */}
            <div className="space-y-2">
              <Label htmlFor="edit-enabled" className="text-[#b3b3b3] font-medium text-sm">
                {t('status')}
              </Label>
              <div className="flex items-center gap-3 h-10">
                <Switch
                  id="edit-enabled"
                  checked={editEnabled}
                  onCheckedChange={setEditEnabled}
                />
                <span className="text-sm text-[#b3b3b3] font-medium">
                  {editEnabled ? t('statusEnabled') : t('statusDisabled')}
                </span>
              </div>
            </div>

            {/* Daily Limit Field */}
            <div className="space-y-2">
              <Label htmlFor="edit-daily-limit" className="text-[#b3b3b3] font-medium text-sm">
                {t('dailyLimitLabel')}
              </Label>
              <Input
                id="edit-daily-limit"
                type="number"
                min={user?.is_admin ? "0" : "1"}
                max={defaultDailyTokenLimit?.toString() || "999999999"}
                step="1"
                value={editDailyLimit}
                onChange={(e) => setEditDailyLimit(e.target.value)}
                className=" border border-[#282828] h-10"
                placeholder={t('dailyLimitPlaceholder')}
              />
              <p className="text-xs text-[#b3b3b3]">
                {defaultDailyTokenLimit
                  ? t('dailyLimitHint', { max: defaultDailyTokenLimit })
                  : t('unlimited')}
              </p>
            </div>
          </div>
          <DialogFooter className="pt-2">
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} className="">
              {tButtons('cancel')}
            </Button>
            <Button onClick={handleSaveEdit} className="">
              {tButtons('save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
