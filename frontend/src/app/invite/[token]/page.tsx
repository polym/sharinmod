'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { CheckCircle2, XCircle, Building2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/lib/store';
import { organizationAPI } from '@/lib/services';

interface InviteInfo {
  organization_name: string;
  organization_slug: string;
  expires_at: string;
  is_valid: boolean;
}

export default function InvitePage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const router = useRouter();
  const { isAuthenticated, setShowLoginDialog, setRedirectAfterLogin, setMyOrganizations } = useAuthStore();

  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [infoError, setInfoError] = useState<string | null>(null);

  const [accepting, setAccepting] = useState(false);
  const [acceptSuccess, setAcceptSuccess] = useState(false);
  const [acceptError, setAcceptError] = useState<string | null>(null);

  useEffect(() => {
    loadInviteInfo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadInviteInfo = async () => {
    setLoadingInfo(true);
    setInfoError(null);
    try {
      const response = await organizationAPI.getInviteInfo(token);
      setInviteInfo(response.data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        setInfoError('邀请链接不存在或已失效');
      } else {
        setInfoError('加载邀请信息失败，请稍后重试');
      }
    } finally {
      setLoadingInfo(false);
    }
  };

  const handleAccept = async () => {
    if (!isAuthenticated) {
      setRedirectAfterLogin(`/invite/${token}`);
      setShowLoginDialog(true);
      return;
    }

    setAccepting(true);
    setAcceptError(null);
    try {
      await organizationAPI.acceptInvite(token);
      setAcceptSuccess(true);
      // B-3: Refresh org store so OrganizationSwitcher reflects the newly joined org
      try {
        const orgsResponse = await organizationAPI.getMyOrganizations();
        setMyOrganizations(orgsResponse.data);
      } catch {
        // Non-fatal: store will be refreshed on next navigation
      }
    } catch (error: any) {
      setAcceptError(error.response?.data?.detail || '接受邀请失败，请稍后重试');
    } finally {
      setAccepting(false);
    }
  };

  if (loadingInfo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="flex items-center gap-2 text-indigo-600">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>加载邀请信息中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg border-indigo-100">
        {infoError ? (
          <>
            <CardHeader className="text-center">
              <XCircle className="w-12 h-12 text-red-400 mx-auto mb-2" />
              <CardTitle className="text-red-600">邀请链接无效</CardTitle>
              <CardDescription>{infoError}</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Button variant="outline" onClick={() => router.push('/marketplace')}>返回首页</Button>
            </CardContent>
          </>
        ) : inviteInfo && !inviteInfo.is_valid ? (
          <>
            <CardHeader className="text-center">
              <XCircle className="w-12 h-12 text-amber-400 mx-auto mb-2" />
              <CardTitle className="text-amber-600">邀请链接已失效</CardTitle>
              <CardDescription>
                邀请链接已过期或已被使用，请联系私服创建者重新发送邀请。
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Button variant="outline" onClick={() => router.push('/marketplace')}>返回首页</Button>
            </CardContent>
          </>
        ) : acceptSuccess ? (
          <>
            <CardHeader className="text-center">
              <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
              <CardTitle className="text-green-600">加入成功！</CardTitle>
              <CardDescription>
                您已成功加入私服「{inviteInfo?.organization_name}」。
                现在可以在顶部切换到该私服。
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Button onClick={() => router.push('/marketplace')} className="bg-indigo-600 hover:bg-indigo-700">
                前往首页
              </Button>
            </CardContent>
          </>
        ) : (
          <>
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Building2 className="w-6 h-6 text-indigo-600" />
              </div>
              <CardTitle>您被邀请加入私服</CardTitle>
              <CardDescription>
                <span className="font-semibold text-gray-700">{inviteInfo?.organization_name}</span>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!isAuthenticated && (
                <p className="text-sm text-amber-600 bg-amber-50 rounded-lg p-3 border border-amber-200">
                  请先登录后再接受邀请
                </p>
              )}
              {acceptError && (
                <p className="text-sm text-red-600 bg-red-50 rounded-lg p-3 border border-red-200">
                  {acceptError}
                </p>
              )}
              <Button
                className="w-full bg-indigo-600 hover:bg-indigo-700"
                onClick={handleAccept}
                disabled={accepting}
              >
                {accepting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    处理中...
                  </>
                ) : isAuthenticated ? '接受邀请' : '登录后接受邀请'}
              </Button>
              <Button variant="outline" className="w-full" onClick={() => router.push('/marketplace')}>
                暂不加入
              </Button>
            </CardContent>
          </>
        )}
      </Card>
    </div>
  );
}
