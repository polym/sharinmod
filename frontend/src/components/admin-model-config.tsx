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
import Image from 'next/image';
import { Edit, Cpu } from 'lucide-react';
import { modelConfigAPI } from '@/lib/services';
import { getProviderLogo } from '@/lib/providers';
import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';

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

export function AdminModelConfig() {
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

  // Derived: filtered model list — fuzzy search on provider_key or model_key
  const filteredModels = useMemo(() => {
    if (!filterQuery.trim()) return models;
    const q = filterQuery.toLowerCase().trim();
    return models.filter(
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
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-purple-600" />
          <CardTitle>{t('title')}</CardTitle>
        </div>
        <CardDescription>{t('description')}</CardDescription>
      </CardHeader>

      <CardContent>
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
                <TableHead>{t('columns.displayName')}</TableHead>
                <TableHead>{t('columns.contextLength')}</TableHead>
                <TableHead>{t('columns.maxOutput')}</TableHead>
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
                          width={16}
                          height={16}
                          className="object-contain rounded-sm"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                        <span className="font-mono text-sm text-gray-500">{model.provider_key}/</span>
                        <span className="font-mono text-sm font-medium">{model.model_key}</span>
                      </div>
                    </TableCell>
                    <TableCell>{model.display_name}</TableCell>
                    <TableCell>{model.context_length}</TableCell>
                    <TableCell>{model.max_output_length}</TableCell>
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
                  <TableCell colSpan={9} className="text-center text-gray-500 py-8">
                    —
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>

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
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? t('editDialog.saving') : t('editDialog.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
