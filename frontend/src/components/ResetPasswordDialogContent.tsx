'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { passwordResetAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { AxiosError } from 'axios';

interface ResetPasswordDialogContentProps {
  token: string | null;
  onSuccess?: () => void;
  onCancel?: () => void;
}

// Password validation regex
const PASSWORD_REGEX = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  digit: /\d/,
};

// Type for API error response
interface ApiError {
  detail?: string | { msg: string }[] | unknown;
}

type ViewState = 'verifying' | 'form' | 'error';

export function ResetPasswordDialogContent({ token, onSuccess, onCancel }: ResetPasswordDialogContentProps) {
  const t = useTranslations('passwordReset');
  const tPassword = useTranslations('password');
  const tCommon = useTranslations('common');
  const router = useRouter();
  const { toast } = useToast();

  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [viewState, setViewState] = useState<ViewState>('verifying');
  const [errorMessage, setErrorMessage] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (!token) {
      setViewState('error');
      setErrorMessage(t('invalidLink'));
      return;
    }

    const verifyToken = async () => {
      try {
        const response = await passwordResetAPI.verifyToken(token);
        setEmail(response.data.email);
        setViewState('form');
      } catch (error: any) {
        setViewState('error');
        const axiosError = error as AxiosError<ApiError>;
        const errorData = axiosError.response?.data;
        if (typeof errorData?.detail === 'string') {
          setErrorMessage(errorData.detail);
        } else {
          setErrorMessage(t('tokenExpiredOrUsed'));
        }
      }
    };

    verifyToken();
  }, [token, t]);

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
      await passwordResetAPI.setPassword(token!, newPassword);

      toast({
        title: t('success'),
        description: t('passwordSet'),
      });

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/shared');
        onSuccess?.();
      }, 2000);
    } catch (error: any) {
      const axiosError = error as AxiosError<ApiError>;
      const errorData = axiosError.response?.data;
      let errorMessage = t('passwordSetFailed');
      if (typeof errorData?.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData?.detail)) {
        errorMessage = errorData.detail.map((e: any) => e.msg).join(', ');
      }
      toast({
        title: t('error'),
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (viewState === 'verifying') {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-[#b3b3b3]">{tCommon('loading')}...</div>
      </div>
    );
  }

  if (viewState === 'error') {
    return (
      <div className="text-center py-4">
        <p className="text-red-600 mb-4">{errorMessage}</p>
        <Button onClick={() => router.push('/shared')} className="w-full">
          {t('backToHome')}
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Username/Email field for browser password manager */}
      <div className="space-y-2">
        <Label htmlFor="username">{tCommon('email')}</Label>
        <Input
          id="username"
          name="username"
          type="text"
          value={email}
          readOnly
          className="bg-[#282828] cursor-not-allowed"
          autoComplete="username"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="new-password">{tPassword('newPassword')}</Label>
        <Input
          id="new-password"
          name="new-password"
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
          autoComplete="new-password"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirm-password">{tPassword('confirmPassword')}</Label>
        <Input
          id="confirm-password"
          name="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          minLength={8}
          maxLength={72}
          placeholder={tPassword('confirmPasswordPlaceholder')}
          autoComplete="new-password"
        />
      </div>

      {/* Password requirements hint */}
      <div className="text-sm text-[#b3b3b3] space-y-1">
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

      <div className="flex gap-2">
        <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
          {tCommon('cancel')}
        </Button>
        <Button type="submit" disabled={loading} className="flex-1">
          {loading ? t('setting') : t('setPassword')}
        </Button>
      </div>
    </form>
  );
}
