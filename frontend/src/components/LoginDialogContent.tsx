'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/services';
import { AxiosError } from 'axios';
import { useTranslations } from 'next-intl';
import GithubIcon from '@/components/icons/github-icon';
import GitlabIcon from '@/components/icons/gitlab-icon';

interface LoginDialogContentProps {
  onSuccess?: () => void;
}

// Simple email validation regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Type for API error response
interface ApiError {
  detail?: string | { msg: string }[] | unknown;
}

// OAuth provider type
interface OAuthProvider {
  id: string;
  name: string;
  enabled: boolean;
  login_url: string;
}

export function LoginDialogContent({ onSuccess }: LoginDialogContentProps) {
  const t = useTranslations('auth');
  const tValidation = useTranslations('auth.validation');
  const tToast = useTranslations('auth.toast');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [error, setError] = useState('');
  const [oauthProviders, setOauthProviders] = useState<OAuthProvider[]>([]);
  const [providersError, setProvidersError] = useState('');
  const login = useAuthStore((state) => state.login);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);
  const setShowChangePasswordDialog = useAuthStore((state) => state.setShowChangePasswordDialog);
  const redirectAfterLogin = useAuthStore((state) => state.redirectAfterLogin);
  const setRedirectAfterLogin = useAuthStore((state) => state.setRedirectAfterLogin);
  const router = useRouter();

  // Load available OAuth providers on mount
  useEffect(() => {
    authAPI.getOAuthProviders().then(response => {
      setOauthProviders(response.data.providers || []);
      setProvidersError('');
    }).catch(err => {
      console.error('Failed to load OAuth providers:', err);
      setProvidersError(t('loadProvidersFailed'));
    });
  }, []);

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
      const response = await authAPI.login({ email, password });
      const { access_token, user, force_password_change } = response.data;
      login(user, access_token);
      // 跳转到登录前的页面或默认页面
      const redirectPath = redirectAfterLogin || '/shared';
      setRedirectAfterLogin(null);
      router.push(redirectPath);
      setShowLoginDialog(false);
      onSuccess?.();

      // 如果需要强制修改密码，显示修改密码弹窗
      if (force_password_change) {
        setShowChangePasswordDialog(true);
      } else {
        router.push('/shared');
      }
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
        setError(tToast('loginFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGithubLogin = () => {
    setOauthLoading(true);
    // 跳转到后端 OAuth 端点，使用相对路径
    window.location.href = '/api/oauth/github/login';
  };

  const handleGitlabLogin = () => {
    setOauthLoading(true);
    // 跳转到后端 OAuth 端点，使用相对路径
    window.location.href = '/api/oauth/gitlab/login';
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="dialog-email">{t('email')}</Label>
        <Input
          id="dialog-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder={t('emailPlaceholder')}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="dialog-password">{t('password')}</Label>
        <Input
          id="dialog-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          placeholder={t('passwordPlaceholder')}
        />
      </div>
      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}
      {providersError && (
        <div className="text-yellow-600 text-sm">{providersError}</div>
      )}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? t('loggingIn') : t('login')}
      </Button>

      <div className="relative my-4">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-[#181818] text-[#b3b3b3]">{t('or')}</span>
        </div>
      </div>

      {oauthProviders.length > 0 ? (
        oauthProviders.map(provider => (
          <Button
            key={provider.id}
            type="button"
            variant="outline"
            className="w-full mb-3 last:mb-0"
            onClick={() => {
              if (provider.id === 'github') {
                handleGithubLogin();
              } else if (provider.id === 'gitlab') {
                handleGitlabLogin();
              }
            }}
            disabled={oauthLoading || loading}
          >
            {oauthLoading && (
              <span className="animate-spin mr-2">
                <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </span>
            )}
            {!oauthLoading && provider.id === 'github' && <GithubIcon className="h-4 w-4 mr-2" />}
            {!oauthLoading && provider.id === 'gitlab' && <GitlabIcon className="h-4 w-4 mr-2" />}
            {t('loginWithProvider', { provider: provider.name })}
          </Button>
        ))
      ) : (
        <div className="text-center text-sm text-[#b3b3b3]">
          {t('noLoginMethods')}
        </div>
      )}

    </form>
  );
}
