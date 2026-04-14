'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';
import { apiKeyAPI } from '@/lib/services';
import { PROVIDER_LIST, getProviderLogo, getProviderBrandName } from '@/lib/providers';
import Image from 'next/image';

interface DiscoveredAPIKey {
  id: number;
  provider: string;
  provider_username: string;
  total_uses: number;
  created_at: string;
  status: string;
}

export function APIKeyDiscovery() {
  const t = useTranslations('discovery');
  const tToast = useTranslations('discovery.toast');
  const tCommon = useTranslations('common');
  const [apiKeys, setAPIKeys] = useState<DiscoveredAPIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [providerFilter, setProviderFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const loadAPIKeys = async (pageNum = 1, provider = 'all') => {
    try {
      const response = await apiKeyAPI.discoverAPIKeys({
        page: pageNum,
        limit: 10,
        provider: provider === 'all' ? undefined : provider,
      });

      if (pageNum === 1) {
        setAPIKeys(response.data.items);
      } else {
        setAPIKeys(prev => [...prev, ...response.data.items]);
      }

      setHasMore(response.data.items.length === 10);
    } catch (error: any) {
      toast({
        title: tToast('error'),
        description: tToast('loadFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAPIKeys(1, providerFilter);
  }, [providerFilter]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadAPIKeys(nextPage, providerFilter);
  };

  const handleProviderFilter = (value: string) => {
    setProviderFilter(value);
    setPage(1);
  };

  const handleUseAPIKey = async (apiKeyId: number) => {
    // For now, redirect to chat page - in a real implementation,
    // you might want to create a unified API key first or handle this differently
    router.push(`/chat?apiKeyId=${apiKeyId}`);
  };

  return (
    <div className="space-y-6">
      <Card className=" border border-[#282828] bg-[#181818]">
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-2">
              <h3 className="text-2xl font-bold leading-none tracking-tight text-white">{t('title')}</h3>
              <p className="text-sm text-[#b3b3b3] font-medium">{t('description')}</p>
            </div>
            <Select value={providerFilter} onValueChange={handleProviderFilter}>
              <SelectTrigger className=" w-[200px] border border-[#282828]">
                {providerFilter === 'all' ? (
                  <SelectValue placeholder={t('selectProvider')} />
                ) : (
                  <div className="flex items-center gap-2">
                    <Image src={getProviderLogo(providerFilter)} alt={getProviderBrandName(providerFilter)} width={20} height={20} />
                    <span>{getProviderBrandName(providerFilter)}</span>
                  </div>
                )}
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all" className="pl-2">{t('allProviders')}</SelectItem>
                {PROVIDER_LIST.map((p) => (
                  <SelectItem key={p.code} value={p.code} className="pl-2">
                    <div className="flex items-center gap-2">
                      <Image src={p.logoPath} alt={p.brandName} width={20} height={20} />
                      <span>{p.brandName}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>

          {loading && apiKeys.length === 0 ? (
            <div className="text-center py-8 text-[#b3b3b3] font-medium">{t('loading')}</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-[#b3b3b3] font-medium">
              {t('noKeys')}
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((apiKey) => (
                <Card key={apiKey.id} className=" border border-[#282828] bg-[#181818]">
                  <CardContent className="pt-5">
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl overflow-hidden shadow-md border-2 border-white bg-[#181818] p-1">
                            <Image src={getProviderLogo(apiKey.provider)} alt={getProviderBrandName(apiKey.provider)} width={40} height={40} className="w-full h-full object-contain" />
                          </div>
                          <div className="font-bold text-lg text-white">{getProviderBrandName(apiKey.provider)}</div>
                        </div>
                        <div className="text-sm text-[#b3b3b3]">
                          {t('provider')}: <span className="font-medium">{apiKey.provider_username}</span>
                        </div>
                        <div className="text-sm text-[#b3b3b3]">
                          {t('uses')}: <span className="font-semibold text-white">{apiKey.total_uses}</span>
                        </div>
                        <div className="text-sm text-[#b3b3b3]">
                          {t('createdAt')}: <span className="font-medium">{new Date(apiKey.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className={` ${apiKey.status === 'active' ? '' : ''}`}>
                          {apiKey.status}
                        </div>
                        <Button
                          onClick={() => handleUseAPIKey(apiKey.id)}
                          disabled={apiKey.status !== 'active'}
                          className=""
                        >
                          {t('use')}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {hasMore && (
                <div className="text-center pt-4">
                  <Button onClick={handleLoadMore} className="">
                    {t('loadMore')}
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
