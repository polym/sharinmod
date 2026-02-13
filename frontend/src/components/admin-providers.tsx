'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/components/ui/toast';
import { Edit, Trash2, Power, PowerOff, Plus, LayoutGrid } from 'lucide-react';
import { adminAPI } from '@/lib/services';
import { Switch } from '@/components/ui/switch';
import { useTranslations } from 'next-intl';

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
  const [modelsDialogOpen, setModelsDialogOpen] = useState(false);

  const [editProvider, setEditProvider] = useState<ProviderConfig | null>(null);
  const [editModels, setEditModels] = useState<ProviderModel[]>([]);

  // Form states
  const [providerKey, setProviderKey] = useState('');
  const [name, setName] = useState('');
  const [website, setWebsite] = useState('');
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
    if (!providerKey || !name || !website) {
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

  const handleToggleModel = async (model: ProviderModel) => {
    try {
      if (model.is_enabled) {
        await adminAPI.disableProviderModel(model.id);
        toast({ title: tToast('success'), description: tToast('modelDisableSuccess') });
      } else {
        await adminAPI.enableProviderModel(model.id);
        toast({ title: tToast('success'), description: tToast('modelEnableSuccess') });
      }
      loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('modelToggleFailed'),
        variant: 'destructive',
      });
    }
  };

  const openEditDialog = (provider: ProviderConfig) => {
    setEditProvider(provider);
    setName(provider.name);
    setWebsite(provider.website);
    setLogoFile(null);
    setEditDialogOpen(true);
  };

  const openModelsDialog = (provider: ProviderConfig) => {
    setEditProvider(provider);
    setEditModels([...provider.models]);
    setModelsDialogOpen(true);
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
                            onClick={() => openModelsDialog(provider)}
                          >
                            <LayoutGrid className="w-4 h-4" />
                          </Button>
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

      {/* Models Management Dialog */}
      <Dialog open={modelsDialogOpen} onOpenChange={setModelsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('manageModels')}</DialogTitle>
            <DialogDescription>{editProvider?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {editModels.map((model) => (
              <Card key={model.id}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-semibold">{model.display_name}</div>
                      <div className="text-sm text-gray-600 font-mono">{model.model_key}</div>
                      {model.description && (
                        <div className="text-sm text-gray-500 mt-1">{model.description}</div>
                      )}
                    </div>
                    <Switch
                      checked={model.is_enabled}
                      onCheckedChange={() => handleToggleModel(model)}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
