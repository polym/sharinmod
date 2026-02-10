'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/services';
import { AxiosError } from 'axios';
import { useTranslations } from 'next-intl';

interface RegisterDialogContentProps {
  onSuccess?: () => void;
}

// Simple email validation regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Type for API error response
interface ApiError {
  detail?: string | { msg: string }[] | unknown;
}

export function RegisterDialogContent({ onSuccess }: RegisterDialogContentProps) {
  const t = useTranslations('auth');
  const tValidation = useTranslations('auth.validation');
  const tToast = useTranslations('auth.toast');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const setShowRegisterDialog = useAuthStore((state) => state.setShowRegisterDialog);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);

  const validateForm = (): boolean => {
    if (!email.trim()) {
      setError(tValidation('enterEmail'));
      return false;
    }
    if (!EMAIL_REGEX.test(email)) {
      setError(tValidation('enterValidEmail'));
      return false;
    }
    if (!password.trim()) {
      setError(tValidation('enterPassword'));
      return false;
    }
    if (password.length < 8) {
      setError(tValidation('passwordMinLength'));
      return false;
    }
    if (!confirmPassword.trim()) {
      setError(tValidation('confirmPassword'));
      return false;
    }
    if (password !== confirmPassword) {
      setError(tValidation('passwordMismatch'));
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await authAPI.register({ email, password });
      // 注册成功后切换到登录弹窗
      setShowRegisterDialog(false);
      setShowLoginDialog(true);
      onSuccess?.();
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const errorData = axiosError.response?.data;
      if (typeof errorData?.detail === 'string') {
        setError(errorData.detail);
      } else if (Array.isArray(errorData?.detail)) {
        setError(errorData.detail.map((e: any) => e.msg).join(', '));
      } else if (errorData?.detail) {
        setError(JSON.stringify(errorData.detail));
      } else {
        setError(tToast('registerFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const switchToLogin = () => {
    setShowRegisterDialog(false);
    setShowLoginDialog(true);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="register-email">{t('email')}</Label>
        <Input
          id="register-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder={t('emailPlaceholder')}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="register-password">{t('password')}</Label>
        <Input
          id="register-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          placeholder={t('passwordPlaceholder')}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="register-confirm-password">{t('confirmPassword')}</Label>
        <Input
          id="register-confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          placeholder={t('passwordPlaceholder')}
        />
      </div>
      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? t('registering') : t('register')}
      </Button>
      <div className="text-center">
        <button
          type="button"
          onClick={switchToLogin}
          className="text-blue-600 hover:underline text-sm"
        >
          {t('hasAccount')}
        </button>
      </div>
    </form>
  );
}
