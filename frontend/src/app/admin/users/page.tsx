'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, ShieldOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/lib/store';
import { adminAPI } from '@/lib/services';
import type { User } from '@/lib/store';

export default function AdminUsersPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 检查用户是否已登录
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    // 检查用户是否为管理员
    if (currentUser?.is_admin) {
      loadUsers();
    } else {
      // 非管理员用户重定向到首页
      router.push('/marketplace');
    }
  }, [currentUser, isAuthenticated]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await adminAPI.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGrantAdmin = async (userId: number) => {
    try {
      await adminAPI.grantAdmin(userId);
      loadUsers();
    } catch (error) {
      console.error('Failed to grant admin:', error);
    }
  };

  const handleRevokeAdmin = async (userId: number) => {
    try {
      await adminAPI.revokeAdmin(userId);
      loadUsers();
    } catch (error) {
      console.error('Failed to revoke admin:', error);
    }
  };

  if (!currentUser?.is_admin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Access denied</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">用户管理</h1>
      {loading ? (
        <div className="text-gray-500">加载中...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.name || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {u.is_admin ? (
                      <Badge variant="default">Admin</Badge>
                    ) : (
                      <Badge variant="secondary">User</Badge>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {u.id !== currentUser?.id && (
                      u.is_admin ? (
                        <Button
                          onClick={() => handleRevokeAdmin(u.id)}
                          size="sm"
                          variant="outline"
                        >
                          <ShieldOff className="w-4 h-4 mr-1" />
                          撤销
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleGrantAdmin(u.id)}
                          size="sm"
                        >
                          <Shield className="w-4 h-4 mr-1" />
                          授权
                        </Button>
                      )
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
