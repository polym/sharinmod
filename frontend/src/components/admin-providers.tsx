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
  const [modelsDialogOpen, setModelsDialogOpen] = useState(false);
  const [modelEditDialogOpen, setModelEditDialogOpen] = useState(false);
  const [deleteModelDialogOpen, setDeleteModelDialogOpen] = useState(false);

  const [editProvider, setEditProvider] = useState<ProviderConfig | null>(null);
  const [editModel, setEditModel] = useState<ProviderModel | null>(null);
  const [deleteModel, setDeleteModel] = useState<ProviderModel | null>(null);
  const [editModels, setEditModels] = useState<ProviderModel[]>([]);

  // Form states
  const [providerKey, setProviderKey] = useState('');
  const [name, setName] = useState('');
  const [website, setWebsite] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [customLlmProvider, setCustomLlmProvider] = useState('openai');
  const [logoFile, setLogoFile] = useState<File | null>(null);

  // Model loading state
  const [isSavingModel, setIsSavingModel] = useState(false);

  // Model form states
  const [modelKey, setModelKey] = useState('');
  const [modelDisplayName, setModelDisplayName] = useState('');
  const [modelDescription, setModelDescription] = useState('');
  const [contextLength, setContextLength] = useState('');
  const [maxOutputLength, setMaxOutputLength] = useState('');
  const [inputTypes, setInputTypes] = useState('');
  const [outputTypes, setOutputTypes] = useState('');
  const [codingScore, setCodingScore] = useState('');

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

  const openCreateModelDialog = () => {
    setEditModel(null);
    setModelKey('');
    setModelDisplayName('');
    setModelDescription('');
    setContextLength('');
    setMaxOutputLength('');
    setInputTypes('');
    setOutputTypes('');
    setCodingScore('');
    setModelEditDialogOpen(true);
  };

  const openEditModelDialog = (model: ProviderModel) => {
    setEditModel(model);
    setModelKey(model.model_key);
    setModelDisplayName(model.display_name);
    setModelDescription(model.description || '');
    setContextLength(model.context_length);
    setMaxOutputLength(model.max_output_length);
    setInputTypes(model.input_types?.join(', ') || '');
    setOutputTypes(model.output_types?.join(', ') || '');
    setCodingScore(model.coding_score?.toString() || '');
    setModelEditDialogOpen(true);
  };

  const handleSaveModel = async () => {
    if (!modelKey || !modelDisplayName || !contextLength || !maxOutputLength) {
      toast({
        title: tToast('error'),
        description: tToast('fillRequired'),
        variant: 'destructive',
      });
      return;
    }

    if (!editModel && !editProvider) {
      toast({
        title: tToast('error'),
        description: 'Provider not found',
        variant: 'destructive',
      });
      return;
    }

    setIsSavingModel(true);
    try {
      const modelData = {
        model_key: modelKey,
        display_name: modelDisplayName,
        description: modelDescription || undefined,
        context_length: contextLength,
        max_output_length: maxOutputLength,
        input_types: inputTypes ? inputTypes.split(',').map(s => s.trim()).filter(Boolean) : undefined,
        output_types: outputTypes ? outputTypes.split(',').map(s => s.trim()).filter(Boolean) : undefined,
        coding_score: codingScore ? parseInt(codingScore) : undefined,
      };

      if (editModel) {
        // Update existing model
        await adminAPI.updateModel(editModel.id, modelData);
        toast({ title: tToast('success'), description: tToast('modelUpdateSuccess') });
      } else {
        // Create new model
        await adminAPI.createModel(editProvider!.id, modelData);
        toast({ title: tToast('success'), description: tToast('modelCreateSuccess') });
      }

      setModelEditDialogOpen(false);
      await loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('modelSaveFailed'),
        variant: 'destructive',
      });
    } finally {
      setIsSavingModel(false);
    }
  };

  const openDeleteModelDialog = (model: ProviderModel) => {
    setDeleteModel(model);
    setDeleteModelDialogOpen(true);
  };

  const handleDeleteModel = async () => {
    if (!deleteModel) return;

    try {
      await adminAPI.deleteModel(deleteModel.id);
      toast({ title: tToast('success'), description: tToast('modelDeleteSuccess') });
      setDeleteModelDialogOpen(false);
      await loadProviders();
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: error.response?.data?.detail || tToast('modelDeleteFailed'),
        variant: 'destructive',
      });
    }
  };

  const openEditDialog = (provider: ProviderConfig) => {
    setEditProvider(provider);
    setName(provider.name);
    setWebsite(provider.website);
    setBaseUrl(provider.base_url || '');
    setCustomLlmProvider(provider.custom_llm_provider || 'openai');
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
                    <Label htmlFor="base-url">Base URL *</Label>
                    <Input
                      id="base-url"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.example.com/v1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="custom-llm-provider">LiteLLM Provider Type</Label>
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
              <Label htmlFor="edit-base-url">Base URL</Label>
              <Input
                id="edit-base-url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.example.com/v1"
              />
            </div>
            <div>
              <Label htmlFor="edit-custom-llm-provider">LiteLLM Provider Type</Label>
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
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>{t('manageModels')}</DialogTitle>
                <DialogDescription>{editProvider?.name}</DialogDescription>
              </div>
              <Button onClick={openCreateModelDialog} size="sm">
                <Plus className="w-4 h-4 mr-2" />
                {t('addModel')}
              </Button>
            </div>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {editModels.length === 0 ? (
              <div className="text-center py-8 text-gray-500">{t('noModels')}</div>
            ) : (
              editModels.map((model) => (
                <Card key={model.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-semibold">{model.display_name}</div>
                        <div className="text-sm text-gray-600 font-mono">{model.model_key}</div>
                        {model.description && (
                          <div className="text-sm text-gray-500 mt-1">{model.description}</div>
                        )}
                        <div className="text-xs text-gray-400 mt-1">
                          {t('contextLength')}: {model.context_length} | {t('maxOutput')}: {model.max_output_length}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={model.is_enabled}
                          onCheckedChange={() => handleToggleModel(model)}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModelDialog(model)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDeleteModelDialog(model)}
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Model Edit Dialog */}
      <Dialog open={modelEditDialogOpen} onOpenChange={setModelEditDialogOpen}>
        <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editModel ? t('editModel') : t('addModel')}</DialogTitle>
            <DialogDescription>{editProvider?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="model-key">{t('modelKey')}</Label>
              <Input
                id="model-key"
                value={modelKey}
                onChange={(e) => setModelKey(e.target.value)}
                placeholder="e.g., gpt-4"
                disabled={!!editModel}
              />
            </div>
            <div>
              <Label htmlFor="model-display-name">{t('displayName')}</Label>
              <Input
                id="model-display-name"
                value={modelDisplayName}
                onChange={(e) => setModelDisplayName(e.target.value)}
                placeholder={t('displayNamePlaceholder')}
              />
            </div>
            <div>
              <Label htmlFor="model-description">{t('description')}</Label>
              <Textarea
                id="model-description"
                value={modelDescription}
                onChange={(e) => setModelDescription(e.target.value)}
                placeholder={t('descriptionPlaceholder')}
                rows={2}
              />
            </div>
            <div>
              <Label htmlFor="context-length">{t('contextLength')}</Label>
              <Input
                id="context-length"
                value={contextLength}
                onChange={(e) => setContextLength(e.target.value)}
                placeholder="e.g., 128k"
              />
            </div>
            <div>
              <Label htmlFor="max-output-length">{t('maxOutput')}</Label>
              <Input
                id="max-output-length"
                value={maxOutputLength}
                onChange={(e) => setMaxOutputLength(e.target.value)}
                placeholder="e.g., 4k"
              />
            </div>
            <div>
              <Label htmlFor="input-types">{t('inputTypes')}</Label>
              <Input
                id="input-types"
                value={inputTypes}
                onChange={(e) => setInputTypes(e.target.value)}
                placeholder="text, image, audio"
              />
              <p className="text-xs text-gray-500 mt-1">{t('commaSeparated')}</p>
            </div>
            <div>
              <Label htmlFor="output-types">{t('outputTypes')}</Label>
              <Input
                id="output-types"
                value={outputTypes}
                onChange={(e) => setOutputTypes(e.target.value)}
                placeholder="text, image"
              />
              <p className="text-xs text-gray-500 mt-1">{t('commaSeparated')}</p>
            </div>
            <div>
              <Label htmlFor="coding-score">{t('codingScore')}</Label>
              <Input
                id="coding-score"
                type="number"
                value={codingScore}
                onChange={(e) => setCodingScore(e.target.value)}
                placeholder="e.g., 85"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModelEditDialogOpen(false)} disabled={isSavingModel}>
              {t('cancel')}
            </Button>
            <Button onClick={handleSaveModel} disabled={isSavingModel}>
              {isSavingModel ? t('loading') : t('save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Model Confirmation Dialog */}
      <Dialog open={deleteModelDialogOpen} onOpenChange={setDeleteModelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('deleteModel')}</DialogTitle>
            <DialogDescription>
              {t('confirmDeleteModel')}: {deleteModel?.display_name} ({deleteModel?.model_key})
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteModelDialogOpen(false)}>
              {t('cancel')}
            </Button>
            <Button variant="destructive" onClick={handleDeleteModel}>
              {t('delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
