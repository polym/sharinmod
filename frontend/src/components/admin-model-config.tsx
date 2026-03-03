'use client';

import { useEffect, useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Image from 'next/image';
import { Edit, Trash2, Type, Image as ImageIcon, Video, Mic, File, Upload } from 'lucide-react';
import { modelConfigAPI, globalModelAPI } from '@/lib/services';
import { getProviderLogo, getModelLogo } from '@/lib/providers';
import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Text': Type,
  'Image': ImageIcon,
  'Video': Video,
  'Audio': Mic,
  'File': File,
};

export interface ModelCatalogItem {
  db_id: number | null;
  provider_key: string;
  provider_name: string;
  model_key: string;
  display_name: string;
  description?: string;
  context_length: string;
  max_output_length: string;
  input_types?: string[];
  output_types?: string[];
  coding_score?: number;
  is_enabled: boolean;
  source: 'db' | 'builtin';
}

interface EditForm {
  display_name: string;
  description: string;
  context_length: string;
  max_output_length: string;
  coding_score: string;
  input_types: string[];
  output_types: string[];
}

// ==================== Global Model Types ====================

interface SupportedProviderInfo {
  provider_key: string;
  name: string;
  logo_path: string | null;
}

interface GlobalModelItem {
  id: number;
  model_key: string;
  display_name: string;
  description?: string;
  context_length: string;
  max_output_length: string;
  input_types?: string[];
  output_types?: string[];
  coding_score?: number;
  logo_url?: string;
  supported_providers: SupportedProviderInfo[];
}

interface GlobalModelForm {
  model_key: string;
  display_name: string;
  description: string;
  context_length: string;
  max_output_length: string;
  coding_score: string;
  input_types: string[];
  output_types: string[];
  logo_file: File | null;
  logo_preview: string;
}

// ==================== Provider Model Tab ====================

function ProviderModelTab() {
  const t = useTranslations('adminModelConfig');
  const { toast } = useToast();

  const [models, setModels] = useState<ModelCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterQuery, setFilterQuery] = useState<string>('');
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ModelCatalogItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [conflictFields, setConflictFields] = useState<Set<keyof EditForm>>(new Set());
  const [editForm, setEditForm] = useState<EditForm>({
    display_name: '',
    description: '',
    context_length: '',
    max_output_length: '',
    coding_score: '',
    input_types: [],
    output_types: [],
  });

  // Derived: filtered model list — fuzzy search on provider_key or model_key, sorted by provider then model
  const filteredModels = useMemo(() => {
    const sorted = [...models].sort((a, b) => a.provider_key.localeCompare(b.provider_key) || a.model_key.localeCompare(b.model_key));
    if (!filterQuery.trim()) return sorted;
    const q = filterQuery.toLowerCase().trim();
    return sorted.filter(
      (m) => m.provider_key.toLowerCase().includes(q) || m.model_key.toLowerCase().includes(q)
    );
  }, [models, filterQuery]);

  const loadModels = async () => {
    setLoading(true);
    try {
      const resp = await modelConfigAPI.getModelCatalog();
      setModels(resp.data.items || []);
    } catch {
      toast({ title: t('toast.error'), description: t('toast.loadFailed'), variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggle = async (model: ModelCatalogItem, checked: boolean) => {
    try {
      if (model.source === 'db' && model.db_id !== null) {
        if (checked) {
          await modelConfigAPI.enableModel(model.db_id);
        } else {
          await modelConfigAPI.disableModel(model.db_id);
        }
      } else {
        // Built-in model: override via model-catalog/override endpoint
        await modelConfigAPI.overrideModel({
          provider_key: model.provider_key,
          model_key: model.model_key,
          is_enabled: checked,
        });
      }
      toast({ description: t('toast.toggleSuccess') });
      await loadModels();
    } catch {
      toast({ title: t('toast.error'), description: t('toast.toggleFailed'), variant: 'destructive' });
    }
  };

  const handleEdit = (model: ModelCatalogItem) => {
    setEditTarget(model);
    setConflictFields(new Set());
    setEditForm({
      display_name: model.display_name || '',
      description: model.description || '',
      context_length: model.context_length || '',
      max_output_length: model.max_output_length || '',
      coding_score: model.coding_score != null ? String(model.coding_score) : '',
      input_types: model.input_types || [],
      output_types: model.output_types || [],
    });
    setEditDialogOpen(true);
  };

  const handleBatchEdit = () => {
    const targets = models.filter((m) => selectedKeys.has(`${m.provider_key}/${m.model_key}`));
    const conflicts = new Set<keyof EditForm>();

    const unifyStr = (getValue: (m: ModelCatalogItem) => string, key: keyof EditForm): string => {
      const vals = targets.map(getValue);
      if (vals.every((v) => v === vals[0])) return vals[0];
      conflicts.add(key);
      return '';
    };

    const unifyArr = (getValue: (m: ModelCatalogItem) => string[], key: keyof EditForm): string[] => {
      const vals = targets.map((m) => [...getValue(m)].sort().join(','));
      if (vals.every((v) => v === vals[0])) return targets[0] ? getValue(targets[0]) : [];
      conflicts.add(key);
      return [];
    };

    setEditTarget(null);
    setConflictFields(conflicts);
    setEditForm({
      display_name: unifyStr((m) => m.display_name || '', 'display_name'),
      description: unifyStr((m) => m.description || '', 'description'),
      context_length: unifyStr((m) => m.context_length || '', 'context_length'),
      max_output_length: unifyStr((m) => m.max_output_length || '', 'max_output_length'),
      coding_score: unifyStr((m) => (m.coding_score != null ? String(m.coding_score) : ''), 'coding_score'),
      input_types: unifyArr((m) => m.input_types || [], 'input_types'),
      output_types: unifyArr((m) => m.output_types || [], 'output_types'),
    });
    setEditDialogOpen(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const parsedScore = editForm.coding_score ? parseInt(editForm.coding_score, 10) : undefined;
      const parsedInputTypes = editForm.input_types.length > 0 ? editForm.input_types : undefined;
      const parsedOutputTypes = editForm.output_types.length > 0 ? editForm.output_types : undefined;

      const payload = {
        display_name: editForm.display_name || undefined,
        description: editForm.description || undefined,
        context_length: editForm.context_length || undefined,
        max_output_length: editForm.max_output_length || undefined,
        input_types: parsedInputTypes,
        output_types: parsedOutputTypes,
        coding_score: parsedScore,
      };

      // 确定要更新的目标列表（单条 or 批量）
      const targets = editTarget
        ? [editTarget]
        : models.filter((m) => selectedKeys.has(`${m.provider_key}/${m.model_key}`));

      await Promise.all(
        targets.map((model) => {
          if (model.source === 'db' && model.db_id !== null) {
            return modelConfigAPI.updateModel(model.db_id, payload);
          } else {
            return modelConfigAPI.overrideModel({
              provider_key: model.provider_key,
              model_key: model.model_key,
              ...payload,
            });
          }
        })
      );

      toast({ description: t('toast.updateSuccess') });
      setEditDialogOpen(false);
      setSelectedKeys(new Set());
      await loadModels();
    } catch {
      toast({ title: t('toast.error'), description: t('toast.updateFailed'), variant: 'destructive' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
        {/* 搜索 + 批量编辑按钮 */}
        <div className="flex gap-3 mb-4 items-center">
          <Input
            className="w-64"
            placeholder={t('filter.searchPlaceholder')}
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
          />
          {selectedKeys.size > 0 && (
            <Button variant="outline" size="sm" onClick={handleBatchEdit}>
              {t('filter.batchEdit', { count: selectedKeys.size })}
            </Button>
          )}
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">{t('loading')}</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={
                      filteredModels.length === 0
                        ? false
                        : filteredModels.every((m) => selectedKeys.has(`${m.provider_key}/${m.model_key}`))
                          ? true
                          : filteredModels.some((m) => selectedKeys.has(`${m.provider_key}/${m.model_key}`))
                            ? 'indeterminate'
                            : false
                    }
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedKeys(new Set(filteredModels.map((m) => `${m.provider_key}/${m.model_key}`)));
                      } else {
                        setSelectedKeys(new Set());
                      }
                    }}
                  />
                </TableHead>
                <TableHead>{t('columns.model')}</TableHead>
                <TableHead>{t('columns.contextMaxOutput')}</TableHead>
                <TableHead>{t('columns.source')}</TableHead>
                <TableHead>{t('columns.status')}</TableHead>
                <TableHead>{t('columns.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredModels.map((model) => {
                const rowKey = `${model.provider_key}/${model.model_key}`;
                const logoPath = getProviderLogo(model.provider_key);
                return (
                  <TableRow key={rowKey}>
                    <TableCell>
                      <Checkbox
                        checked={selectedKeys.has(rowKey)}
                        onCheckedChange={(checked) => {
                          const next = new Set(selectedKeys);
                          if (checked) next.add(rowKey);
                          else next.delete(rowKey);
                          setSelectedKeys(next);
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Image
                          src={logoPath}
                          alt={model.provider_key}
                          width={20}
                          height={20}
                          className="object-contain rounded-sm shrink-0"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                        <div>
                          <div className="font-mono text-sm"><span className="text-gray-500">{model.provider_key}/</span><span className="font-medium">{model.model_key}</span></div>
                          <div className="text-xs text-gray-500">{model.display_name}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{model.context_length} / {model.max_output_length}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={model.source === 'db' ? 'default' : 'secondary'}>
                        {t(`source.${model.source}`)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={model.is_enabled}
                        onCheckedChange={(checked) => handleToggle(model, checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(model)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
              {filteredModels.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-gray-500 py-8">
                    —
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{t('editDialog.title')}</DialogTitle>
            <DialogDescription>
              {editTarget
                ? t('editDialog.description', { modelKey: editTarget.model_key })
                : t('editDialog.batchEditNote', { count: selectedKeys.size })}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t('editDialog.displayName')}</Label>
              <Input
                value={editForm.display_name}
                onChange={(e) => setEditForm((f) => ({ ...f, display_name: e.target.value }))}
              />
              {!editTarget && conflictFields.has('display_name') && (
                <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
              )}
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.modelDescription')}</Label>
              <Textarea
                value={editForm.description}
                onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                rows={3}
              />
              {!editTarget && conflictFields.has('description') && (
                <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-2">
                <Label>{t('editDialog.contextLength')}</Label>
                <Input
                  value={editForm.context_length}
                  onChange={(e) => setEditForm((f) => ({ ...f, context_length: e.target.value }))}
                  placeholder="128k"
                />
                {!editTarget && conflictFields.has('context_length') && (
                  <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
                )}
              </div>
              <div className="grid gap-2">
                <Label>{t('editDialog.maxOutput')}</Label>
                <Input
                  value={editForm.max_output_length}
                  onChange={(e) => setEditForm((f) => ({ ...f, max_output_length: e.target.value }))}
                  placeholder="4k"
                />
                {!editTarget && conflictFields.has('max_output_length') && (
                  <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
                )}
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.codingScore')}</Label>
              <Input
                type="number"
                value={editForm.coding_score}
                onChange={(e) => setEditForm((f) => ({ ...f, coding_score: e.target.value }))}
                placeholder="1400"
              />
              {!editTarget && conflictFields.has('coding_score') && (
                <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
              )}
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.inputTypesLabel')}</Label>
              <div className="flex flex-wrap gap-3">
                {['Text', 'Image', 'Audio', 'Video'].map((type) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <Checkbox
                      id={`input-${type}`}
                      checked={editForm.input_types.includes(type)}
                      onCheckedChange={(checked) => {
                        setEditForm((f) => ({
                          ...f,
                          input_types: checked
                            ? [...f.input_types, type]
                            : f.input_types.filter((v) => v !== type),
                        }));
                      }}
                    />
                    <Label htmlFor={`input-${type}`} className="font-normal cursor-pointer">{type}</Label>
                  </div>
                ))}
              </div>
              {!editTarget && conflictFields.has('input_types') && (
                <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
              )}
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.outputTypesLabel')}</Label>
              <div className="flex flex-wrap gap-3">
                {['Text', 'Image', 'Audio', 'Video'].map((type) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <Checkbox
                      id={`output-${type}`}
                      checked={editForm.output_types.includes(type)}
                      onCheckedChange={(checked) => {
                        setEditForm((f) => ({
                          ...f,
                          output_types: checked
                            ? [...f.output_types, type]
                            : f.output_types.filter((v) => v !== type),
                        }));
                      }}
                    />
                    <Label htmlFor={`output-${type}`} className="font-normal cursor-pointer">{type}</Label>
                  </div>
                ))}
              </div>
              {!editTarget && conflictFields.has('output_types') && (
                <p className="text-xs text-amber-600">{t('editDialog.conflictHint')}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={isSaving}>
              {t('editDialog.cancel')}
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? t('editDialog.saving') : t('editDialog.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ==================== Global Model Tab ====================

function GlobalModelTab() {
  const t = useTranslations('adminGlobalModel');
  const { toast } = useToast();

  const [models, setModels] = useState<GlobalModelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterQuery, setFilterQuery] = useState<string>('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<GlobalModelItem | null>(null);
  const [editTarget, setEditTarget] = useState<GlobalModelItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState<GlobalModelForm>({
    model_key: '',
    display_name: '',
    description: '',
    context_length: '',
    max_output_length: '',
    coding_score: '',
    input_types: [],
    output_types: [],
  });

  const loadModels = async () => {
    setLoading(true);
    try {
      const resp = await globalModelAPI.list();
      setModels(resp.data || []);
    } catch {
      toast({ title: t('toast.loadFailed'), variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openAddDialog = () => {
    setEditTarget(null);
    setForm({ model_key: '', display_name: '', description: '', context_length: '', max_output_length: '', coding_score: '', input_types: [], output_types: [], logo_file: null, logo_preview: '' });
    setDialogOpen(true);
  };

  const openEditDialog = (item: GlobalModelItem) => {
    setEditTarget(item);
    setForm({
      model_key: item.model_key,
      display_name: item.display_name,
      description: item.description || '',
      context_length: item.context_length,
      max_output_length: item.max_output_length,
      coding_score: item.coding_score != null ? String(item.coding_score) : '',
      input_types: item.input_types || [],
      output_types: item.output_types || [],
      logo_file: null,
      logo_preview: item.logo_url || '',
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload = {
        model_key: form.model_key,
        display_name: form.display_name,
        description: form.description || undefined,
        context_length: form.context_length,
        max_output_length: form.max_output_length,
        coding_score: form.coding_score ? parseInt(form.coding_score, 10) : undefined,
        input_types: form.input_types.length > 0 ? form.input_types : undefined,
        output_types: form.output_types.length > 0 ? form.output_types : undefined,
        logo: form.logo_file || undefined,
      };

      if (editTarget) {
        await globalModelAPI.update(editTarget.id, payload);
        toast({ description: t('toast.updateSuccess') });
      } else {
        await globalModelAPI.create(payload as Parameters<typeof globalModelAPI.create>[0]);
        toast({ description: t('toast.createSuccess') });
      }
      setDialogOpen(false);
      await loadModels();
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast({
        title: editTarget ? t('toast.updateFailed') : t('toast.createFailed'),
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = (item: GlobalModelItem) => {
    setDeleteTarget(item);
  };

  const filteredModels = useMemo(() => {
    const sorted = [...models].sort((a, b) => a.model_key.localeCompare(b.model_key));
    if (!filterQuery.trim()) return sorted;
    const q = filterQuery.toLowerCase().trim();
    return sorted.filter(
      (m) => m.model_key.toLowerCase().includes(q) || m.display_name.toLowerCase().includes(q)
    );
  }, [models, filterQuery]);

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await globalModelAPI.delete(deleteTarget.id);
      toast({ description: t('toast.deleteSuccess') });
      setDeleteTarget(null);
      await loadModels();
    } catch {
      toast({ title: t('toast.deleteFailed'), variant: 'destructive' });
    }
  };

  return (
    <>
        <div className="flex gap-3 mb-4 items-center">
          <Input
            className="w-64"
            placeholder={t('filter.searchPlaceholder')}
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
          />
          <Button size="sm" onClick={openAddDialog}>
            {t('addButton')}
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">{t('loading')}</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('columns.model')}</TableHead>
                <TableHead>{t('columns.supportedProviders')}</TableHead>
                <TableHead>{t('columns.contextMaxOutput')}</TableHead>
                <TableHead>{t('columns.codingScore')}</TableHead>
                <TableHead>{t('columns.inputTypes')}</TableHead>
                <TableHead>{t('columns.outputTypes')}</TableHead>
                <TableHead>{t('columns.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredModels.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-md overflow-hidden flex-shrink-0 bg-gray-50 dark:bg-gray-800 flex items-center justify-center">
                        <Image
                          src={item.logo_url || getModelLogo(item.model_key)}
                          alt={item.display_name}
                          width={32}
                          height={32}
                          className="object-contain"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            if (target.parentElement) {
                              target.parentElement.innerHTML = `<span class="text-xs font-bold text-gray-400">${item.model_key.charAt(0).toUpperCase()}</span>`;
                            }
                          }}
                        />
                      </div>
                      <div>
                        <div className="font-medium text-sm">{item.display_name}</div>
                        <div className="font-mono text-xs text-gray-500">{item.model_key}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {item.supported_providers.length === 0 ? (
                      <span className="text-xs text-gray-400">{t('noProviders')}</span>
                    ) : (
                      <div className="flex items-center">
                        {item.supported_providers.slice(0, 5).map((p, i) => (
                          <div
                            key={p.provider_key}
                            className={cn('w-6 h-6 rounded-full border border-white overflow-hidden bg-white', i > 0 && '-ml-2')}
                            title={p.name}
                          >
                            <Image
                              src={getProviderLogo(p.provider_key)}
                              alt={p.name}
                              width={24}
                              height={24}
                              className="object-contain"
                              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                          </div>
                        ))}
                        {item.supported_providers.length > 5 && (
                          <span className="ml-1 text-xs text-gray-500">+{item.supported_providers.length - 5}</span>
                        )}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{item.context_length} / {item.max_output_length}</span>
                  </TableCell>
                  <TableCell>
                    {item.coding_score != null ? (
                      <span className="text-sm font-mono">{item.coding_score}</span>
                    ) : (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {(item.input_types || []).map((type) => {
                        const Icon = TYPE_ICONS[type];
                        return Icon ? (
                          <div key={type} title={type} className="inline-flex items-center justify-center w-6 h-6 rounded border border-gray-300 dark:border-gray-500 text-gray-700 dark:text-gray-300">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                        ) : null;
                      })}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {(item.output_types || []).map((type) => {
                        const Icon = TYPE_ICONS[type];
                        return Icon ? (
                          <div key={type} title={type} className="inline-flex items-center justify-center w-6 h-6 rounded border border-gray-300 dark:border-gray-500 text-gray-700 dark:text-gray-300">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                        ) : null;
                      })}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openEditDialog(item)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <span title={item.supported_providers.length > 0 ? t('deleteTooltip') : undefined}>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={item.supported_providers.length > 0}
                          onClick={() => handleDelete(item)}
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {filteredModels.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-gray-500 py-8">—</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editTarget ? t('dialog.editTitle') : t('dialog.addTitle')}</DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t('dialog.modelKey')}</Label>
              <Input
                value={form.model_key}
                onChange={(e) => setForm((f) => ({ ...f, model_key: e.target.value }))}
                placeholder={t('dialog.modelKeyPlaceholder')}
                readOnly={!!editTarget}
                className={editTarget ? 'bg-gray-50 cursor-not-allowed' : ''}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t('dialog.logo')}</Label>
              <div className="flex items-center gap-3">
                {form.logo_preview && (
                  <div className="w-12 h-12 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 flex-shrink-0">
                    <Image
                      src={form.logo_preview}
                      alt="Logo preview"
                      width={48}
                      height={48}
                      className="object-contain w-full h-full"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                  </div>
                )}
                <div className="flex flex-col gap-1 flex-1">
                  <label className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors w-fit">
                    <Upload className="w-3.5 h-3.5" />
                    {t('dialog.logoUpload')}
                    <input
                      type="file"
                      accept="image/png,image/jpeg"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setForm((f) => ({
                            ...f,
                            logo_file: file,
                            logo_preview: URL.createObjectURL(file),
                          }));
                        }
                      }}
                    />
                  </label>
                  <span className="text-xs text-gray-400">{t('dialog.logoHint')}</span>
                </div>
                {form.logo_preview && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-red-500 hover:text-red-600"
                    onClick={() => setForm((f) => ({ ...f, logo_file: null, logo_preview: '' }))}
                  >
                    {t('dialog.logoRemove')}
                  </Button>
                )}
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t('dialog.displayName')}</Label>
              <Input
                value={form.display_name}
                onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t('dialog.description')}</Label>
              <Textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-2">
                <Label>{t('dialog.contextLength')}</Label>
                <Input
                  value={form.context_length}
                  onChange={(e) => setForm((f) => ({ ...f, context_length: e.target.value }))}
                  placeholder="128k"
                />
              </div>
              <div className="grid gap-2">
                <Label>{t('dialog.maxOutput')}</Label>
                <Input
                  value={form.max_output_length}
                  onChange={(e) => setForm((f) => ({ ...f, max_output_length: e.target.value }))}
                  placeholder="4k"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t('dialog.codingScore')}</Label>
              <Input
                type="number"
                value={form.coding_score}
                onChange={(e) => setForm((f) => ({ ...f, coding_score: e.target.value }))}
                placeholder="1400"
              />
            </div>
            <div className="grid gap-2">
              <Label>{t('dialog.inputTypes')}</Label>
              <div className="flex flex-wrap gap-3">
                {['Text', 'Image', 'Audio', 'Video'].map((type) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <Checkbox
                      id={`gm-input-${type}`}
                      checked={form.input_types.includes(type)}
                      onCheckedChange={(checked) => {
                        setForm((f) => ({
                          ...f,
                          input_types: checked ? [...f.input_types, type] : f.input_types.filter((v) => v !== type),
                        }));
                      }}
                    />
                    <Label htmlFor={`gm-input-${type}`} className="font-normal cursor-pointer">{type}</Label>
                  </div>
                ))}
              </div>
            </div>
            <div className="grid gap-2">
              <Label>{t('dialog.outputTypes')}</Label>
              <div className="flex flex-wrap gap-3">
                {['Text', 'Image', 'Audio', 'Video'].map((type) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <Checkbox
                      id={`gm-output-${type}`}
                      checked={form.output_types.includes(type)}
                      onCheckedChange={(checked) => {
                        setForm((f) => ({
                          ...f,
                          output_types: checked ? [...f.output_types, type] : f.output_types.filter((v) => v !== type),
                        }));
                      }}
                    />
                    <Label htmlFor={`gm-output-${type}`} className="font-normal cursor-pointer">{type}</Label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={isSaving}>
              {t('dialog.cancel')}
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? t('dialog.saving') : t('dialog.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{t('deleteDialogTitle')}</DialogTitle>
            <DialogDescription>
              {deleteTarget && t('deleteConfirm', { modelKey: deleteTarget.model_key })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              {t('dialog.cancel')}
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              {t('deleteConfirmButton')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ==================== Main Component ====================

export function AdminModelConfig() {
  const t = useTranslations('adminModelConfig');

  return (
    <Tabs defaultValue="provider">
      <Card>
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-1.5">
              <CardTitle>{t('title')}</CardTitle>
              <CardDescription>{t('description')}</CardDescription>
            </div>
            <TabsList>
              <TabsTrigger value="provider">{t('tabs.provider')}</TabsTrigger>
              <TabsTrigger value="global">{t('tabs.global')}</TabsTrigger>
            </TabsList>
          </div>
        </CardHeader>
        <CardContent>
          <TabsContent value="provider" className="mt-0">
            <ProviderModelTab />
          </TabsContent>
          <TabsContent value="global" className="mt-0">
            <GlobalModelTab />
          </TabsContent>
        </CardContent>
      </Card>
    </Tabs>
  );
}
