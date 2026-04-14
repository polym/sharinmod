'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { useAuthStore, useLocaleStore } from '@/lib/store';
import { authAPI, userAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';

export function SettingsPage() {
  const t = useTranslations('settings');
  const tApiKeys = useTranslations('apiKeys');
  const tCommon = useTranslations('common');

  return (
    <div className="space-y-6">
      <LanguageSettingsCard />
      <ProfileSettings />
    </div>
  );
}

export function LanguageSettingsCard() {
  const t = useTranslations('settings');
  const tLang = useTranslations('language');

  return (
    <Card>
      <CardHeader className="p-6">
        <CardTitle>{t('languageSettings')}</CardTitle>
        <CardDescription>
          {t('languageSettings')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">{t('language')}:</span>
          <LanguageSelector />
        </div>
      </CardContent>
    </Card>
  );
}

function LanguageSelector() {
  const t = useTranslations('settings');
  const { locale, setLocale } = useLocaleStore();
  const tLang = useTranslations('language');

  const languageOptions = [
    { value: 'zh-CN', label: tLang('zh-CN') },
    { value: 'en', label: tLang('en') },
  ];

  return (
    <select
      value={locale}
      onChange={(e) => setLocale(e.target.value as 'zh-CN' | 'en')}
      className="border rounded-md px-3 py-2 text-sm"
    >
      {languageOptions.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

interface ProfileSettingsProps {
  onSaveSuccess?: () => void;
}

export function ProfileSettings({ onSaveSuccess }: ProfileSettingsProps) {
  const t = useTranslations('settings');
  const tApiKeys = useTranslations('apiKeys');
  const tCommon = useTranslations('common');

  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { user, updateUser } = useAuthStore();
  const { toast } = useToast();

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
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [updateUser]);

  useEffect(() => {
    if (user) {
      setEmail(user.email || '');
      setName(user.name || '');
      setBio(user.bio || '');
    }
  }, [user]);

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
      onSaveSuccess?.();
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

  if (loading) {
    return <div className="text-center py-8">{tCommon('loading')}</div>;
  }

  return (
    <Card>
      <CardHeader className="p-6">
        <CardTitle>{t('profileSettings')}</CardTitle>
        <CardDescription>
          {t('profileDescription')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="email">{t('email')}</Label>
          <Input
            id="email"
            type="email"
            value={email}
            disabled
            className="bg-[#1f1f1f]"
          />
          <p className="text-sm text-[#b3b3b3]">{t('emailNotEditable')}</p>
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
      </CardContent>
    </Card>
  );
}
