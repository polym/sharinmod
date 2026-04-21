'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { useAuthStore } from '@/lib/store';
import { userAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';

// Password validation regex
const PASSWORD_REGEX = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  digit: /\d/,
};

interface ChangePasswordDialogContentProps {
  onSuccess?: () => void;
}

export function ChangePasswordDialogContent({ onSuccess }: ChangePasswordDialogContentProps) {
  const t = useTranslations('password');
  const tSettings = useTranslations('settings');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const { user, updateUser } = useAuthStore();
  const { toast } = useToast();
  const router = useRouter();

  const validatePassword = (password: string): string[] => {
    const validationErrors: string[] = [];

    if (password.length < 8) {
      validationErrors.push(t('errors.minLength'));
    }
    if (password.length > 72) {
      validationErrors.push(t('errors.maxLength'));
    }
    if (!PASSWORD_REGEX.uppercase.test(password)) {
      validationErrors.push(t('errors.uppercase'));
    }
    if (!PASSWORD_REGEX.lowercase.test(password)) {
      validationErrors.push(t('errors.lowercase'));
    }
    if (!PASSWORD_REGEX.digit.test(password)) {
      validationErrors.push(t('errors.digit'));
    }

    return validationErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    // Validate password
    const validationErrors = validatePassword(newPassword);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    // Check passwords match
    if (newPassword !== confirmPassword) {
      setErrors([t('errors.mismatch')]);
      return;
    }

    setLoading(true);

    try {
      await userAPI.changePassword({ new_password: newPassword });

      // Update user state to clear force_password_change flag
      if (user) {
        updateUser({ ...user, force_password_change: false });
      }

      toast({
        title: tSettings('toast.success'),
        description: t('changeSuccess'),
      });

      onSuccess?.();
      router.push('/shared');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || t('changeFailed');
      toast({
        title: tSettings('toast.error'),
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="new-password" required>{t('newPassword')}</Label>
        <Input
          id="new-password"
          type="password"
          value={newPassword}
          onChange={(e) => {
            setNewPassword(e.target.value);
            setErrors([]);
          }}
          required
          minLength={8}
          maxLength={72}
          placeholder={t('newPasswordPlaceholder')}
          autoComplete="new-password"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirm-password" required>{t('confirmPassword')}</Label>
        <Input
          id="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          minLength={8}
          maxLength={72}
          placeholder={t('confirmPasswordPlaceholder')}
          autoComplete="new-password"
        />
      </div>

      {/* Password requirements hint */}
      <div className="text-sm text-[#b3b3b3] space-y-1">
        <p className="font-medium">{t('requirements')}:</p>
        <ul className="list-disc list-inside space-y-0.5">
          <li className={newPassword.length >= 8 && newPassword.length <= 72 ? 'text-green-600' : ''}>
            {t('requirementsList.length')}
          </li>
          <li className={PASSWORD_REGEX.uppercase.test(newPassword) ? 'text-green-600' : ''}>
            {t('requirementsList.uppercase')}
          </li>
          <li className={PASSWORD_REGEX.lowercase.test(newPassword) ? 'text-green-600' : ''}>
            {t('requirementsList.lowercase')}
          </li>
          <li className={PASSWORD_REGEX.digit.test(newPassword) ? 'text-green-600' : ''}>
            {t('requirementsList.digit')}
          </li>
        </ul>
      </div>

      {/* Error messages */}
      {errors.length > 0 && (
        <div className="text-red-600 text-sm space-y-1">
          {errors.map((error, index) => (
            <p key={index}>• {error}</p>
          ))}
        </div>
      )}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? tSettings('saving') : t('changePassword')}
      </Button>
    </form>
  );
}