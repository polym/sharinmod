'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/services';
import { AxiosError } from 'axios';

interface LoginDialogContentProps {
  onSuccess?: () => void;
}

// Simple email validation regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Type for API error response
interface ApiError {
  detail?: string | { msg: string }[] | unknown;
}

export function LoginDialogContent({ onSuccess }: LoginDialogContentProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const login = useAuthStore((state) => state.login);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);

  const validateForm = (): boolean => {
    if (!email.trim()) {
      setError('请输入邮箱地址');
      return false;
    }
    if (!EMAIL_REGEX.test(email)) {
      setError('请输入有效的邮箱地址');
      return false;
    }
    if (!password.trim()) {
      setError('请输入密码');
      return false;
    }
    if (password.length < 8) {
      setError('密码长度至少为 8 位');
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
      const { access_token, user } = response.data;
      login(user, access_token);
      setShowLoginDialog(false);
      onSuccess?.();
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const errorData = axiosError.response?.data;
      if (typeof errorData?.detail === 'string') {
        setError(errorData.detail);
      } else if (Array.isArray(errorData?.detail)) {
        setError(errorData.detail.map((e) => e.msg).join(', '));
      } else if (errorData?.detail) {
        setError(JSON.stringify(errorData.detail));
      } else {
        setError('登录失败，请检查您的凭据');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="dialog-email">邮箱</Label>
        <Input
          id="dialog-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="your@email.com"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="dialog-password">密码</Label>
        <Input
          id="dialog-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          placeholder="••••••••"
        />
      </div>
      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? '登录中...' : '登录'}
      </Button>
    </form>
  );
}
