'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { passwordResetAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';

// Password validation regex
const PASSWORD_REGEX = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  digit: /\d/,
};

export default function ResetPasswordPage() {
  const t = useTranslations('passwordReset');
  const tPassword = useTranslations('password');
  const tCommon = useTranslations('common');

  const searchParams = useSearchParams();
  const router = useRouter();
  const { toast } = useToast();

  const token = searchParams.get('token');
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [valid, setValid] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (!token) {
      setVerifying(false);
      setValid(false);
      return;
    }

    const verifyToken = async () => {
      try {
        const response = await passwordResetAPI.verifyToken(token);
        setEmail(response.data.email);
        setValid(true);
      } catch (error: any) {
        setValid(false);
        toast({
          title: t('invalidToken'),
          description: error.response?.data?.detail || t('tokenExpiredOrUsed'),
          variant: 'destructive',
        });
      } finally {
        setVerifying(false);
      }
    };

    verifyToken();
  }, [token, toast, t]);

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
      await passwordResetAPI.setPassword(token, newPassword);

      toast({
        title: t('success'),
        description: t('passwordSet'),
      });

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/shared');
      }, 2000);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || t('passwordSetFailed');
      toast({
        title: t('error'),
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (verifying) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">{tCommon('loading')}...</div>
      </div>
    );
  }

  if (!valid) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="text-red-600">{t('invalidLink')}</CardTitle>
            <CardDescription>{t('invalidLinkDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push('/shared')} className="w-full">
              {t('backToHome')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader>
          <CardTitle>{t('title')}</CardTitle>
          <CardDescription>
            {t('description').replace('{email}', email)}
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

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? t('setting') : t('setPassword')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}