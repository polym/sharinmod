'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { useAuthStore } from '@/lib/store';
import { authAPI, userAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';

export function ProfileDialog() {
  const showProfileDialog = useAuthStore((state) => state.showProfileDialog);
  const setShowProfileDialog = useAuthStore((state) => state.setShowProfileDialog);
  const { user, updateUser } = useAuthStore();
  const t = useTranslations('settings');
  const tApiKeys = useTranslations('apiKeys');
  const { toast } = useToast();

  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [email, setEmail] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await authAPI.getProfile();
        const userData = response.data;
        updateUser(userData);
        setEmail(userData.email || '');
        setName(userData.name || '');
        setBio(userData.bio || '');
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      }
    };

    if (showProfileDialog) {
      fetchProfile();
    }
  }, [showProfileDialog, updateUser]);

  useEffect(() => {
    if (user && showProfileDialog) {
      setEmail(user.email || '');
      setName(user.name || '');
      setBio(user.bio || '');
    }
  }, [user, showProfileDialog]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await userAPI.updateProfile({
        name,
        bio,
      });

      updateUser(response.data);
      toast({
        title: t('toast.success'),
        description: t('toast.profileUpdateSuccess'),
      });
      setShowProfileDialog(false);
    } catch (error: any) {
      toast({
        title: tApiKeys('toast.error'),
        description: error.response?.data?.message || tApiKeys('toast.updateFailed'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={showProfileDialog} onOpenChange={setShowProfileDialog}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('profileSettings')}</DialogTitle>
          <DialogDescription>
            {t('profileDescription')}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email">{t('email')}</Label>
            <Input
              id="email"
              type="email"
              value={email}
              disabled
              className="bg-gray-50"
            />
            <p className="text-sm text-gray-500">{t('emailNotEditable')}</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">{t('name')}</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('namePlaceholder')}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">{t('bio')}</Label>
            <Textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder={t('bioPlaceholder')}
              rows={4}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? t('saving') : t('saveChanges')}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
