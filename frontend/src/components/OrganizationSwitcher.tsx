'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { useAuthStore, type Organization } from '@/lib/store';
import { organizationAPI } from '@/lib/services';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';
import { useToast } from '@/components/ui/toast';

export function OrganizationSwitcher({ variant = 'header' }: { variant?: 'header' | 'sidebar' }) {
  const t = useTranslations('sidebar');
  const tCommon = useTranslations('common');
  const { toast } = useToast();
  const { currentOrganization, setCurrentOrganization, setShowCreateOrganizationDialog, isAuthenticated, myOrganizations, setMyOrganizations } = useAuthStore();
  const [isSwitching, setIsSwitching] = useState(false);

  // Keep a ref in sync with currentOrganization so that loadOrganizations (a stable
  // useCallback) can read the latest value without being re-created on every org change.
  const currentOrganizationRef = useRef(currentOrganization);
  useEffect(() => {
    currentOrganizationRef.current = currentOrganization;
  });

  // Wrapped in useCallback so the useEffect dependency array can include it without
  // causing infinite re-renders. Zustand setters are stable references.
  const loadOrganizations = useCallback(async () => {
    try {
      const response = await organizationAPI.getMyOrganizations();
      const data = response.data;
      setMyOrganizations(data);

      // 静默回退：若当前私服不在最新列表中，切换回默认（无 toast，因用户未主动发起切换）
      const currentOrg = currentOrganizationRef.current;
      if (currentOrg) {
        const allOrgs = [...data.owned, ...data.joined];
        const stillMember = allOrgs.some(o => o.id === currentOrg.id);
        if (!stillMember) {
          setCurrentOrganization(null);
        }
      }
    } catch (error) {
      console.error('[OrganizationSwitcher] Failed to load organizations:', error);
    }
  }, [setMyOrganizations, setCurrentOrganization]);

  useEffect(() => {
    if (isAuthenticated) {
      loadOrganizations();
    }
  }, [isAuthenticated, loadOrganizations]);

  const handleSelectOrganization = async (org: Organization | null) => {
    if (!org) {
      setCurrentOrganization(null);
      return;
    }

    // Guard against concurrent clicks while a switch is already in progress.
    if (isSwitching) return;
    setIsSwitching(true);

    try {
      const response = await organizationAPI.getMyOrganizations();
      const data = response.data;
      setMyOrganizations(data);

      const allOrgs = [...data.owned, ...data.joined];
      // Use the fresh org object from the API response (F1: avoid stale local state).
      const freshOrg = allOrgs.find(o => o.id === org.id);

      if (!freshOrg) {
        toast({
          title: t('orgNotFound'),
          variant: 'destructive',
        });
        setCurrentOrganization(null);
        return;
      }

      setCurrentOrganization(freshOrg);
    } catch (error) {
      console.error('[OrganizationSwitcher] Failed to verify org access:', error);
      toast({
        title: t('orgSwitchFailed'),
        variant: 'destructive',
      });
    } finally {
      setIsSwitching(false);
    }
  };

  const allOrganizations = [...(myOrganizations?.owned ?? []), ...(myOrganizations?.joined ?? [])];
  const isPublic = !currentOrganization;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={cn(
            'transition-colors cursor-pointer group',
            variant === 'sidebar'
              ? 'w-full flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium bg-[#1f1f1f] hover:bg-[#282828] text-[#b3b3b3] border border-[#4d4d4d]'
              : cn(
                  'flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border-2 transition-all duration-200 min-w-[80px] max-w-[160px] overflow-hidden',
                  isPublic
                    ? 'bg-[#1f1f1f] border-[#4d4d4d] hover:border-[#4d4d4d]'
                    : 'bg-[#282828] border-[#4d4d4d] hover:border-[#4d4d4d]'
                )
          )}
          style={variant === 'header' ? {
            boxShadow: '0 1px 0 rgba(0,0,0,0.3)',
          } : undefined}
        >
          {variant === 'sidebar' ? (
            <>
              <span className="truncate">
                {isPublic ? t('sharedSpace') : currentOrganization?.name || tCommon('unnamed')}
              </span>
              <ChevronDown className="w-4 h-4 flex-shrink-0 text-[#535353] transition-transform duration-200 group-data-[state=open]:rotate-180" />
            </>
          ) : (
            <>
              <span className={cn(
                'text-sm font-semibold truncate',
                isPublic ? 'text-[#b3b3b3]' : 'text-violet-700'
              )}>
                {isPublic ? t('sharedSpace') : currentOrganization?.name || tCommon('unnamed')}
              </span>
              <ChevronDown className={cn(
                'w-3.5 h-3.5 flex-shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180',
                isPublic ? 'text-[#535353]' : 'text-violet-400'
              )} />
            </>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" sideOffset={6} className={variant === 'sidebar' ? 'w-52' : 'w-40'}>
        {/* Public workspace */}
        <DropdownMenuItem
          className="cursor-pointer flex items-center justify-between py-2"
          onClick={() => handleSelectOrganization(null)}
        >
          <span className="text-sm font-medium text-white">{t('sharedSpace')}</span>
          {isPublic && <Check className="w-4 h-4 text-[#b3b3b3] flex-shrink-0" />}
        </DropdownMenuItem>

        {/* Private organizations */}
        {allOrganizations.length > 0 && (
          <>
            <DropdownMenuSeparator />
            {allOrganizations.map((org) => {
              const isSelected = currentOrganization?.id === org.id;
              return (
                <DropdownMenuItem
                  key={org.id}
                  className="cursor-pointer flex items-center justify-between py-2"
                  onClick={() => handleSelectOrganization(org)}
                >
                  <span className="text-sm font-medium text-white truncate">{org.name}</span>
                  {isSelected && <Check className="w-4 h-4 text-violet-500 flex-shrink-0" />}
                </DropdownMenuItem>
              );
            })}
          </>
        )}

        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer flex items-center py-2 text-[#b3b3b3] focus:text-[#b3b3b3]"
          onClick={() => setShowCreateOrganizationDialog(true)}
        >
          <span className="text-sm font-medium">{t('createOrganization')}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}