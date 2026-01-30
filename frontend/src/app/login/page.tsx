'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/services';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authAPI.login({ email, password });
      const { access_token, user } = response.data;
      login(user, access_token);
      router.push('/dashboard');
    } catch (err: any) {
      // 处理不同类型的错误响应
      const errorData = err.response?.data;
      if (typeof errorData?.detail === 'string') {
        setError(errorData.detail);
      } else if (Array.isArray(errorData?.detail)) {
        // Pydantic 验证错误
        setError(errorData.detail.map((e: any) => e.msg).join(', '));
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>登录 SharinMod</CardTitle>
          <CardDescription>
            输入您的凭据来访问平台
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? '登录中...' : '登录'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Link href="/register" className="text-blue-600 hover:underline">
              还没有账户？注册
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}