'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authAPI } from '@/lib/services';
import { AxiosError } from 'axios';
import { useTranslations } from 'next-intl';

interface RegisterDialogContentProps {
  onSwitchToLogin?: () => void;
}

// Simple email validation regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Password validation regex
const PASSWORD_REGEX = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  digit: /\d/,
};

interface ApiError {
  detail?: string | { msg: string }[] | unknown;
}

function SuccessState({ email, onSwitchToLogin, t }: { email: string; onSwitchToLogin?: () => void; t: ReturnType<typeof useTranslations> }) {
  return (
    <div className="space-y-4 text-center py-4">
      <div className="text-4xl">📧</div>
      <h3 className="font-semibold text-lg">{t('successTitle')}</h3>
      <p className="text-sm text-muted-foreground">
        {t('successDescription', { email })}
      </p>
      {onSwitchToLogin && (
        <Button variant="link" className="text-sm" onClick={onSwitchToLogin}>
          {t('switchToLogin')}
        </Button>
      )}
    </div>
  );
}

export function RegisterDialogContent({ onSwitchToLogin }: RegisterDialogContentProps) {
  const t = useTranslations('register');
  const tValidation = useTranslations('register.validation');
  const tErrors = useTranslations('register.errors');
  const searchParams = useSearchParams();

  // Initialize invitation code from URL params
  const inviteCodeParam = searchParams.get('inviteCode');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [invitationCode, setInvitationCode] = useState(inviteCodeParam || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [registered, setRegistered] = useState(false);

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
    if (password.length > 72) {
      setError(tValidation('passwordMaxLength'));
      return false;
    }
    if (!PASSWORD_REGEX.uppercase.test(password)) {
      setError(tValidation('passwordUppercase'));
      return false;
    }
    if (!PASSWORD_REGEX.lowercase.test(password)) {
      setError(tValidation('passwordLowercase'));
      return false;
    }
    if (!PASSWORD_REGEX.digit.test(password)) {
      setError(tValidation('passwordDigit'));
      return false;
    }
    if (!confirmPassword.trim()) {
      setError(tValidation('enterConfirmPassword'));
      return false;
    }
    if (password !== confirmPassword) {
      setError(tValidation('passwordsNotMatch'));
      return false;
    }
    if (!invitationCode.trim()) {
      setError(tValidation('enterInvitationCode'));
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) return;

    setLoading(true);
    try {
      await authAPI.register({ email, password, invitation_code: invitationCode.trim() });
      setRegistered(true);
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const detail = axiosError.response?.data?.detail;
      if (typeof detail === 'string') {
        if (detail.includes('邀请码')) {
          setError(tErrors('invalidCode'));
        } else if (detail.includes('邮箱')) {
          setError(tErrors('emailTaken'));
        } else {
          setError(detail);
        }
      } else {
        setError(tErrors('registerFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  if (registered) {
    return <SuccessState email={email} onSwitchToLogin={onSwitchToLogin} t={t} />;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="reg-email" required>{t('email')}</Label>
        <Input
          id="reg-email"
          name="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('emailPlaceholder')}
          required
          autoComplete="username"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-password" required>{t('password')}</Label>
        <Input
          id="reg-password"
          name="new-password"
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setError('');
          }}
          placeholder={t('passwordPlaceholder')}
          required
          minLength={8}
          maxLength={72}
          autoComplete="new-password"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-confirm-password" required>{t('confirmPassword')}</Label>
        <Input
          id="reg-confirm-password"
          name="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder={t('passwordPlaceholder')}
          required
          minLength={8}
          maxLength={72}
          autoComplete="new-password"
        />
      </div>

      {/* Password requirements hint */}
      <div className="text-sm text-[#b3b3b3] space-y-1">
        <p className="font-medium">{t('requirements')}:</p>
        <ul className="list-disc list-inside space-y-0.5">
          <li className={password.length >= 8 && password.length <= 72 ? 'text-green-600' : ''}>
            {t('requirementsList.length')}
          </li>
          <li className={PASSWORD_REGEX.uppercase.test(password) ? 'text-green-600' : ''}>
            {t('requirementsList.uppercase')}
          </li>
          <li className={PASSWORD_REGEX.lowercase.test(password) ? 'text-green-600' : ''}>
            {t('requirementsList.lowercase')}
          </li>
          <li className={PASSWORD_REGEX.digit.test(password) ? 'text-green-600' : ''}>
            {t('requirementsList.digit')}
          </li>
        </ul>
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-invite-code" required>{t('invitationCode')}</Label>
        <Input
          id="reg-invite-code"
          name="invitation-code"
          type="text"
          value={invitationCode}
          onChange={(e) => setInvitationCode(e.target.value)}
          placeholder={t('invitationCodePlaceholder')}
          required
          autoComplete="off"
        />
      </div>
      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? t('submitting') : t('submit')}
      </Button>
      {onSwitchToLogin && (
        <div className="text-center">
          <Button variant="link" className="text-sm" type="button" onClick={onSwitchToLogin}>
            {t('switchToLogin')}
          </Button>
        </div>
      )}
    </form>
  );
}
