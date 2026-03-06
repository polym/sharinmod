'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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

interface ChangePasswordCardProps {
  forceChange?: boolean;
}

export function ChangePasswordCard({ forceChange = false }: ChangePasswordCardProps) {
  const t = useTranslations('settings');
  const tPassword = useTranslations('password');
  const tCommon = useTranslations('common');

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
      validationErrors.push(tPassword('errors.minLength'));
    }
    if (password.length > 72) {
      validationErrors.push(tPassword('errors.maxLength'));
    }
    if (!PASSWORD_REGEX.uppercase.test(password)) {
      validationErrors.push(tPassword('errors.uppercase'));
    }
    if (!PASSWORD_REGEX.lowercase.test(password)) {
      validationErrors.push(tPassword('errors.lowercase'));
    }
    if (!PASSWORD_REGEX.digit.test(password)) {
      validationErrors.push(tPassword('errors.digit'));
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
      setErrors([tPassword('errors.mismatch')]);
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
        title: t('toast.success'),
        description: tPassword('changeSuccess'),
      });

      // If this was a forced password change, redirect to shared page
      if (forceChange) {
        router.push('/shared');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || tPassword('changeFailed');
      toast({
        title: t('toast.error'),
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className={forceChange ? 'border-orange-500 border-2' : ''}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {tPassword('changePassword')}
          {forceChange && (
            <span className="text-orange-500 text-sm font-normal">
              ({tPassword('required')})
            </span>
          )}
        </CardTitle>
        <CardDescription>
          {forceChange ? tPassword('forceChangeDescription') : tPassword('changeDescription')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new-password">{tPassword('newPassword')}</Label>
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
              placeholder={tPassword('newPasswordPlaceholder')}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm-password">{tPassword('confirmPassword')}</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              maxLength={72}
              placeholder={tPassword('confirmPasswordPlaceholder')}
            />
          </div>

          {/* Password requirements hint */}
          <div className="text-sm text-gray-500 space-y-1">
            <p className="font-medium">{tPassword('requirements')}:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li className={newPassword.length >= 8 && newPassword.length <= 72 ? 'text-green-600' : ''}>
                {tPassword('requirementsList.length')}
              </li>
              <li className={PASSWORD_REGEX.uppercase.test(newPassword) ? 'text-green-600' : ''}>
                {tPassword('requirementsList.uppercase')}
              </li>
              <li className={PASSWORD_REGEX.lowercase.test(newPassword) ? 'text-green-600' : ''}>
                {tPassword('requirementsList.lowercase')}
              </li>
              <li className={PASSWORD_REGEX.digit.test(newPassword) ? 'text-green-600' : ''}>
                {tPassword('requirementsList.digit')}
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

          <div className="flex justify-end">
            <Button type="submit" disabled={loading}>
              {loading ? t('saving') : tPassword('changePassword')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}