'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import api from '@/lib/api';
import { authAPI } from '@/lib/services';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string>('');
  const login = useAuthStore((state) => state.login);
  const redirectAfterLogin = useAuthStore((state) => state.redirectAfterLogin);
  const setRedirectAfterLogin = useAuthStore((state) => state.setRedirectAfterLogin);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const token = searchParams.get('token');
        const error = searchParams.get('error');

        if (error) {
          setError(decodeURIComponent(error));
          return;
        }

        if (!token) {
          setError('No token received from OAuth provider');
          return;
        }

        // 设置 token 到 axios 默认 headers
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        // 使用 token 获取用户信息
        const response = await authAPI.getProfile();
        const user = response.data;

        // 登录并存储 token
        login(user, token);

        // 跳转到登录前的页面或默认页面
        const redirectPath = redirectAfterLogin || '/shared';
        setRedirectAfterLogin(null);
        router.push(redirectPath);
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError('Authentication failed. Please try again.');
      }
    };

    handleCallback();
  }, [searchParams, router, login, redirectAfterLogin, setRedirectAfterLogin]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-8 bg-[#181818] rounded-lg shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h1>
          <p className="text-[#b3b3b3] mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-[#b3b3b3]">Logging you in...</p>
      </div>
    </div>
  );
}
