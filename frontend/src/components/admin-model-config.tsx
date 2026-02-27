'use client';

import { useEffect, useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Edit, Cpu } from 'lucide-react';
import { modelConfigAPI } from '@/lib/services';
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
  input_types: string;
  output_types: string;
}

export function AdminModelConfig() {
  const t = useTranslations('adminModelConfig');
  const { toast } = useToast();

  const [models, setModels] = useState<ModelCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ModelCatalogItem | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [editForm, setEditForm] = useState<EditForm>({
    display_name: '',
    description: '',
    context_length: '',
    max_output_length: '',
    coding_score: '',
    input_types: '',
    output_types: '',
  });

  // Derived: unique provider list for filter
  const providerOptions = useMemo(() => {
    const keys = Array.from(new Set(models.map((m) => m.provider_key)));
    return keys.sort();
  }, [models]);

  // Derived: filtered model list (client-side filtering)
  const filteredModels = useMemo(() => {
    return models.filter((m) => {
      if (filterProvider !== 'all' && m.provider_key !== filterProvider) return false;
      if (filterStatus === 'enabled' && !m.is_enabled) return false;
      if (filterStatus === 'disabled' && m.is_enabled) return false;
      return true;
    });
  }, [models, filterProvider, filterStatus]);

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
    setEditForm({
      display_name: model.display_name || '',
      description: model.description || '',
      context_length: model.context_length || '',
      max_output_length: model.max_output_length || '',
      coding_score: model.coding_score != null ? String(model.coding_score) : '',
      input_types: model.input_types?.join(', ') || '',
      output_types: model.output_types?.join(', ') || '',
    });
    setEditDialogOpen(true);
  };

  const handleSave = async () => {
    if (!editTarget) return;
    setIsSaving(true);
    try {
      const parsedScore = editForm.coding_score ? parseInt(editForm.coding_score, 10) : undefined;
      const parsedInputTypes = editForm.input_types
        ? editForm.input_types.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined;
      const parsedOutputTypes = editForm.output_types
        ? editForm.output_types.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined;

      if (editTarget.source === 'db' && editTarget.db_id !== null) {
        await modelConfigAPI.updateModel(editTarget.db_id, {
          display_name: editForm.display_name || undefined,
          description: editForm.description || undefined,
          context_length: editForm.context_length || undefined,
          max_output_length: editForm.max_output_length || undefined,
          input_types: parsedInputTypes,
          output_types: parsedOutputTypes,
          coding_score: parsedScore,
        });
      } else {
        await modelConfigAPI.overrideModel({
          provider_key: editTarget.provider_key,
          model_key: editTarget.model_key,
          display_name: editForm.display_name || undefined,
          description: editForm.description || undefined,
          context_length: editForm.context_length || undefined,
          max_output_length: editForm.max_output_length || undefined,
          input_types: parsedInputTypes,
          output_types: parsedOutputTypes,
          coding_score: parsedScore,
        });
      }
      toast({ description: t('toast.updateSuccess') });
      setEditDialogOpen(false);
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
        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <Select value={filterProvider} onValueChange={setFilterProvider}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder={t('filter.allProviders')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('filter.allProviders')}</SelectItem>
              {providerOptions.map((pk) => (
                <SelectItem key={pk} value={pk}>{pk}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder={t('filter.allStatus')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('filter.allStatus')}</SelectItem>
              <SelectItem value="enabled">{t('filter.enabled')}</SelectItem>
              <SelectItem value="disabled">{t('filter.disabled')}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">{t('loading')}</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('columns.provider')}</TableHead>
                <TableHead>{t('columns.modelKey')}</TableHead>
                <TableHead>{t('columns.displayName')}</TableHead>
                <TableHead>{t('columns.contextLength')}</TableHead>
                <TableHead>{t('columns.maxOutput')}</TableHead>
                <TableHead>{t('columns.source')}</TableHead>
                <TableHead>{t('columns.status')}</TableHead>
                <TableHead>{t('columns.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredModels.map((model) => (
                <TableRow key={`${model.provider_key}/${model.model_key}`}>
                  <TableCell className="font-medium">{model.provider_key}</TableCell>
                  <TableCell className="font-mono text-sm">{model.model_key}</TableCell>
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
              ))}
              {filteredModels.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-gray-500 py-8">
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
              {t('editDialog.description').replace('{modelKey}', editTarget?.model_key || '')}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>{t('editDialog.displayName')}</Label>
              <Input
                value={editForm.display_name}
                onChange={(e) => setEditForm((f) => ({ ...f, display_name: e.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.description')}</Label>
              <Textarea
                value={editForm.description}
                onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-2">
                <Label>{t('editDialog.contextLength')}</Label>
                <Input
                  value={editForm.context_length}
                  onChange={(e) => setEditForm((f) => ({ ...f, context_length: e.target.value }))}
                  placeholder="128k"
                />
              </div>
              <div className="grid gap-2">
                <Label>{t('editDialog.maxOutput')}</Label>
                <Input
                  value={editForm.max_output_length}
                  onChange={(e) => setEditForm((f) => ({ ...f, max_output_length: e.target.value }))}
                  placeholder="4k"
                />
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
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.inputTypes')}</Label>
              <Input
                value={editForm.input_types}
                onChange={(e) => setEditForm((f) => ({ ...f, input_types: e.target.value }))}
                placeholder="Text, Image"
              />
            </div>
            <div className="grid gap-2">
              <Label>{t('editDialog.outputTypes')}</Label>
              <Input
                value={editForm.output_types}
                onChange={(e) => setEditForm((f) => ({ ...f, output_types: e.target.value }))}
                placeholder="Text"
              />
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
