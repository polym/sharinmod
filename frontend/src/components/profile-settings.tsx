'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { useAuthStore } from '@/lib/store';
import { userAPI } from '@/lib/services';

export function ProfileSettings() {
  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { user, updateUser } = useAuthStore();
  const { toast } = useToast();

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setBio(user.bio || '');
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await userAPI.updateProfile({
        name,
        bio,
      });

      updateUser(response.data);
      toast({
        title: '成功',
        description: '个人资料更新成功',
      });
    } catch (error: any) {
      toast({
        title: '错误',
        description: error.response?.data?.message || '更新失败',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>个人资料设置</CardTitle>
        <CardDescription>
          更新您的个人信息和个人简介
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="email">邮箱</Label>
          <Input
            id="email"
            type="email"
            value={user?.email || ''}
            disabled
            className="bg-gray-50"
          />
          <p className="text-sm text-gray-500">邮箱地址不可修改</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="name">姓名</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="输入您的姓名"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="bio">个人简介</Label>
          <Textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="介绍一下自己..."
            rows={4}
          />
        </div>

        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? '保存中...' : '保存更改'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}