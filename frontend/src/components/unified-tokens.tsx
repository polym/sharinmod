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
import { apiKeyAPI } from '@/lib/services';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useTranslations } from 'next-intl';
import { useLocaleStore } from '@/lib/store';

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
}

export function UnifiedAPIKeys() {
  const t = useTranslations('apiKeys');
  const tButtons = useTranslations('apiKeys.buttons');
  const tToast = useTranslations('apiKeys.toast');
  const tCommon = useTranslations('common');
  const { locale } = useLocaleStore();

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
  const [loadingKeys, setLoadingKeys] = useState<Set<number>>(new Set());
  const [copiedKeyId, setCopiedKeyId] = useState<number | null>(null);
  const { toast } = useToast();

  const loadAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMyUnifiedAPIKeys();
      setAPIKeys(response.data.items);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAPIKeys();
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
      });

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

    try {
      await apiKeyAPI.updateUnifiedAPIKey(editingKey.id, {
        api_key_name: editName,
        description: editDescription,
        status: editEnabled ? 'active' : 'revoked',
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
      <Card>
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-1.5">
              <h3 className="text-xl font-semibold leading-none tracking-tight">{t('title')}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('description')}</p>
            </div>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="ghost" className="bg-brand-100 hover:bg-brand-400 text-brand-500 border border-brand-500">
                  {t('create')}
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>{t('create')}</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                      {t('name')}
                    </Label>
                    <Input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="col-span-3"
                      placeholder={t('namePlaceholder')}
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="description" className="text-right">
                      {t('description')}
                    </Label>
                    <Textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="col-span-3"
                      placeholder={t('descriptionPlaceholder')}
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={handleCreateUnifiedAPIKey}>
                    {tButtons('create')}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">{tCommon('loading')}</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {t('noKeys')}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('name')}</TableHead>
                    <TableHead>API Key</TableHead>
                    <TableHead>{t('status')}</TableHead>
                    <TableHead>{t('createdAt')}</TableHead>
                    <TableHead>{t('lastUsedAt')}</TableHead>
                    <TableHead>{t('actions')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apiKeys.map((apiKey) => (
                    <TableRow key={apiKey.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{apiKey.api_key_name || t('unnamed')}</span>
                          {apiKey.description && (
                            <span
                              className="text-xs text-gray-400 line-clamp-2 break-words"
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
                              <span className="font-mono bg-gray-100 p-1 rounded text-sm">
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
                                  className="h-6 w-6 p-0"
                                >
                                  {copiedKeyId === apiKey.id ? (
                                    <Check className="h-3 w-3 text-purple-600" />
                                  ) : (
                                    <Copy className="h-3 w-3" />
                                  )}
                                </Button>
                                {copiedKeyId === apiKey.id && (
                                  <span className="text-xs text-purple-600 ml-1 inline-block w-16">
                                    {t('copied')}
                                  </span>
                                )}
                              </div>
                            </>
                          ) : (
                            <span className="text-gray-500">{t('noKey')}</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          apiKey.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {apiKey.status === 'active' ? t('statusActive') : t('statusRevoked')}
                        </span>
                      </TableCell>
                      <TableCell>
                        {formatDate(apiKey.created_at)}
                      </TableCell>
                      <TableCell>
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
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUnifiedAPIKey(apiKey.id)}
                            aria-label={tCommon('delete')}
                            disabled={loadingKeys.has(apiKey.id)}
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
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{t('edit')}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-name" className="text-right">
                {t('name')}
              </Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="col-span-3"
                placeholder={t('namePlaceholder')}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-description" className="text-right">
                {t('description')}
              </Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="col-span-3"
                placeholder={t('optionalDescription')}
                rows={3}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-enabled" className="text-right">
                {t('status')}
              </Label>
              <div className="col-span-3 flex items-center gap-2">
                <Switch
                  id="edit-enabled"
                  checked={editEnabled}
                  onCheckedChange={setEditEnabled}
                />
                <span className="text-sm text-gray-600">
                  {editEnabled ? t('statusEnabled') : t('statusDisabled')}
                </span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              {tButtons('cancel')}
            </Button>
            <Button onClick={handleSaveEdit}>
              {tButtons('save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
