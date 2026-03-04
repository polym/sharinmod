'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { Edit, Trash2, Power, PowerOff, Plus } from 'lucide-react';
import { adminAPI } from '@/lib/services';
import { Switch } from '@/components/ui/switch';
import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { getProviderLogo, getProviderDefaults } from '@/lib/providers';

interface ProviderModel {
  id: number;
  model_key: string;
  display_name: string;
  description?: string;
  context_length: string;
  max_output_length: string;
  input_types?: string[];
  output_types?: string[];
  coding_score?: number;
  is_enabled: boolean;
}

interface ProviderConfig {
  id: number;
  provider_key: string;
  name: string;
  website: string;
  logo_path?: string;
  base_url?: string;
  custom_llm_provider?: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  models: ProviderModel[];
}

export function AdminProviders() {
  const t = useTranslations('adminProviders');
  const tToast = useTranslations('adminProviders.toast');
  const { toast } = useToast();

  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [loading, setLoading] = useState(true);

  // Create/Edit dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const [editProvider, setEditProvider] = useState<ProviderConfig | null>(null);

  // Form states
  const [providerKey, setProviderKey] = useState('');
  const [name, setName] = useState('');
  const [website, setWebsite] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [customLlmProvider, setCustomLlmProvider] = useState('openai');
  const [logoFile, setLogoFile] = useState<File | null>(null);

  const loadProviders = async () => {
    try {
      const response = await adminAPI.getProviders();
      setProviders(response.data.items || []);
    } catch (error: any) {
      console.error('Failed to load providers:', error);
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('loadFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProviders();
  }, []);

  const handleCreateProvider = async () => {
    if (!providerKey || !name || !website || !baseUrl) {
      toast({
        title: tToast('error'),
        description: tToast('fillRequired'),
        variant: 'destructive',
      });
      return;
    }

    try {
      await adminAPI.createProvider({
        provider_key: providerKey,
        name,
        website,
        base_url: baseUrl,
        custom_llm_provider: customLlmProvider,
        logo: logoFile || undefined,
        models: [],
      });

      toast({
        title: tToast('success'),
        description: tToast('createSuccess'),
      });

      setCreateDialogOpen(false);
      setProviderKey('');
      setName('');
      setWebsite('');
      setBaseUrl('');
      setCustomLlmProvider('openai');
      setLogoFile(null);
      loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('createFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleUpdateProvider = async () => {
    if (!editProvider) return;

    try {
      await adminAPI.updateProvider(editProvider.id, {
        name: name || editProvider.name,
        website: website || editProvider.website,
        base_url: baseUrl || undefined,
        custom_llm_provider: customLlmProvider || undefined,
        logo: logoFile || undefined,
        is_enabled: undefined,
      });

      toast({
        title: tToast('success'),
        description: tToast('updateSuccess'),
      });

      setEditDialogOpen(false);
      setName('');
      setWebsite('');
      setBaseUrl('');
      setCustomLlmProvider('openai');
      setLogoFile(null);
      loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('updateFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleDeleteProvider = async (id: number) => {
    try {
      await adminAPI.deleteProvider(id);
      toast({
        title: tToast('success'),
        description: tToast('deleteSuccess'),
      });
      loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('deleteFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleToggleProvider = async (provider: ProviderConfig) => {
    try {
      if (provider.is_enabled) {
        await adminAPI.disableProvider(provider.id);
        toast({ title: tToast('success'), description: tToast('disableSuccess') });
      } else {
        await adminAPI.enableProvider(provider.id);
        toast({ title: tToast('success'), description: tToast('enableSuccess') });
      }
      loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('toggleFailed'),
        variant: 'destructive',
      });
    }
  };

  const openEditDialog = (provider: ProviderConfig) => {
    const defaults = getProviderDefaults(provider.provider_key);
    setEditProvider(provider);
    setName(provider.name);
    setWebsite(provider.website);
    setBaseUrl(provider.base_url || defaults?.base_url || '');
    setCustomLlmProvider(provider.custom_llm_provider || defaults?.custom_llm_provider || 'openai');
    setLogoFile(null);
    setEditDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{t('title')}</CardTitle>
              <CardDescription>{t('description')}</CardDescription>
            </div>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={() => {
                  setProviderKey('');
                  setName('');
                  setWebsite('');
                  setBaseUrl('');
                  setCustomLlmProvider('openai');
                  setLogoFile(null);
                }}>
                  <Plus className="w-4 h-4 mr-2" />
                  {t('create')}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{t('create')}</DialogTitle>
                  <DialogDescription>{t('createDialogDesc')}</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label htmlFor="provider-key">{t('providerKey')}</Label>
                    <Input
                      id="provider-key"
                      value={providerKey}
                      onChange={(e) => setProviderKey(e.target.value)}
                      placeholder="e.g., openai"
                    />
                  </div>
                  <div>
                    <Label htmlFor="name">{t('name')}</Label>
                    <Input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder={t('namePlaceholder')}
                    />
                  </div>
                  <div>
                    <Label htmlFor="website">{t('website')}</Label>
                    <Input
                      id="website"
                      value={website}
                      onChange={(e) => setWebsite(e.target.value)}
                      placeholder="https://example.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="custom-llm-provider">接口规范</Label>
                    <select
                      id="custom-llm-provider"
                      value={customLlmProvider}
                      onChange={(e) => setCustomLlmProvider(e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <option value="openai">openai</option>
                      <option value="anthropic">anthropic</option>
                      <option value="openrouter">openrouter</option>
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="base-url">Base URL *</Label>
                    <Input
                      id="base-url"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.example.com/v1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="logo">{t('logo')}</Label>
                    <Input
                      id="logo"
                      type="file"
                      accept="image/png,image/jpeg,image/jpg"
                      onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={handleCreateProvider}>{t('submit')}</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">{t('loading')}</div>
          ) : providers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">{t('noProviders')}</div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10">Logo</TableHead>
                    <TableHead>{t('providerKey')}</TableHead>
                    <TableHead>{t('name')}</TableHead>
                    <TableHead>{t('website')}</TableHead>
                    <TableHead>{t('modelCount')}</TableHead>
                    <TableHead>{t('status')}</TableHead>
                    <TableHead>{t('actions')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {providers.map((provider) => (
                    <TableRow key={provider.id}>
                      <TableCell>
                        <Image
                          src={provider.logo_path || getProviderLogo(provider.provider_key)}
                          alt={provider.name}
                          width={24}
                          height={24}
                          className="rounded-sm object-contain"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm">{provider.provider_key}</TableCell>
                      <TableCell>{provider.name}</TableCell>
                      <TableCell>
                        <a href={provider.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          {provider.website}
                        </a>
                      </TableCell>
                      <TableCell>{provider.models.length}</TableCell>
                      <TableCell>
                        <Switch
                          checked={provider.is_enabled}
                          onCheckedChange={() => handleToggleProvider(provider)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditDialog(provider)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm(t('confirmDelete'))) {
                                handleDeleteProvider(provider.id);
                              }
                            }}
                          >
                            <Trash2 className="w-4 h-4 text-red-600" />
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

      {/* Edit Provider Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('edit')}</DialogTitle>
            <DialogDescription>{t('editDialogDesc')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="edit-name">{t('name')}</Label>
              <Input
                id="edit-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="edit-website">{t('website')}</Label>
              <Input
                id="edit-website"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="edit-custom-llm-provider">接口规范</Label>
              <select
                id="edit-custom-llm-provider"
                value={customLlmProvider}
                onChange={(e) => setCustomLlmProvider(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="openai">openai</option>
                <option value="anthropic">anthropic</option>
                <option value="openrouter">openrouter</option>
              </select>
            </div>
            <div>
              <Label htmlFor="edit-base-url">Base URL</Label>
              <Input
                id="edit-base-url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.example.com/v1"
              />
            </div>
            <div>
              <Label htmlFor="edit-logo">{t('logo')}</Label>
              <Input
                id="edit-logo"
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleUpdateProvider}>{t('submit')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
