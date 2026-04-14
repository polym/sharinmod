'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuthStore } from '@/lib/store';
import { organizationAPI } from '@/lib/services';
import { Building2 } from 'lucide-react';

export function CreateOrganizationDialog() {
  const { showCreateOrganizationDialog, setShowCreateOrganizationDialog, setCurrentOrganization, setMyOrganizations } = useAuthStore();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('请输入组织名称');
      return;
    }

    if (name.length > 100) {
      setError('组织名称不能超过100个字符');
      return;
    }

    setLoading(true);
    try {
      const response = await organizationAPI.createOrganization({ name: name.trim() });
      const newOrganization = response.data;

      // Refresh org list so OrganizationSwitcher shows the newly created org
      try {
        const orgsResponse = await organizationAPI.getMyOrganizations();
        setMyOrganizations(orgsResponse.data);
      } catch {
        // Non-fatal: list will refresh on next load
      }

      // Auto-switch to the newly created organization
      setCurrentOrganization(newOrganization);

      // Close dialog and reset form
      setShowCreateOrganizationDialog(false);
      setName('');
    } catch (error: any) {
      console.error('[CreateOrganizationDialog] Failed to create organization:', error);
      setError(error.response?.data?.detail || '创建私服失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setShowCreateOrganizationDialog(false);
    setName('');
    setError('');
  };

  return (
    <Dialog open={showCreateOrganizationDialog} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>创建私服</DialogTitle>
          <DialogDescription>
            创建一个独立的私服空间来组织和管理您的资源
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="org-name" className="text-sm font-medium text-gray-700">
              私服名称
            </label>
            <div className="relative">
              <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                id="org-name"
                type="text"
                placeholder="输入私服名称"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="pl-10"
                disabled={loading}
                maxLength={100}
                autoFocus
              />
            </div>
            {error && (
              <p className="text-sm text-red-600">{error}</p>
            )}
          </div>
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={loading || !name.trim()}
              className="bg-gradient-to-r from-indigo-500 to-indigo-600 text-white hover:from-indigo-600 hover:to-indigo-700"
            >
              {loading ? '创建中...' : '创建'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}