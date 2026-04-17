'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { useAuthStore, type Organization, type MyOrganizationsData } from '@/lib/store';
import { organizationAPI } from '@/lib/services';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';
import { useToast } from '@/components/ui/toast';

export function OrganizationSwitcher({ variant = 'header' }: { variant?: 'header' | 'sidebar' }) {
  const t = useTranslations('sidebar');
  const tCommon = useTranslations('common');
  const { toast } = useToast();
  const { currentOrganization, setCurrentOrganization, isAuthenticated, myOrganizations, setMyOrganizations } = useAuthStore();
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
      const data = response.data as MyOrganizationsData;
      setMyOrganizations(data);

      // 静默回退：若当前私服不在最新列表中，切换到个人组织
      const currentOrg = currentOrganizationRef.current;
      if (currentOrg) {
        const allOrgs = [...data.owned, ...data.joined];
        const stillMember = allOrgs.some(o => o.id === currentOrg.id);
        if (!stillMember) {
          const personalOrg = data.owned.find(o => o.is_personal);
          // Fall back to first owned org if no personal org (e.g. existing owners pre-migration)
          setCurrentOrganization(personalOrg || data.owned[0] || null);
        }
      } else {
        // Auto-select personal org; fall back to first owned org for pre-existing owners
        const personalOrg = data.owned.find(o => o.is_personal);
        if (personalOrg) {
          setCurrentOrganization(personalOrg);
        } else if (data.owned.length > 0) {
          setCurrentOrganization(data.owned[0]);
        }
      }
    } catch (error) {
      console.error('[OrganizationSwitcher] Failed to load organizations:', error);
      toast({
        title: tCommon('error'),
        variant: 'destructive',
      });
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
      const data = response.data as MyOrganizationsData;
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
  const getOrgDisplayName = (org: Organization) => org.is_personal ? t('personalWorkspace') : org.name;

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
                  'bg-[#282828] border-[#4d4d4d] hover:border-[#4d4d4d]'
                )
          )}
          style={variant === 'header' ? {
            boxShadow: '0 1px 0 rgba(0,0,0,0.3)',
          } : undefined}
        >
          {variant === 'sidebar' ? (
            <>
              <span className="truncate">
                {currentOrganization?.is_personal ? t('personalWorkspace') : (currentOrganization?.name || tCommon('loading'))}
              </span>
              <ChevronDown className="w-4 h-4 flex-shrink-0 text-[#535353] transition-transform duration-200 group-data-[state=open]:rotate-180" />
            </>
          ) : (
            <>
              <span className={cn(
                'text-sm font-semibold truncate',
                'text-[#1ed760]'
              )}>
                {currentOrganization?.is_personal ? t('personalWorkspace') : (currentOrganization?.name || tCommon('loading'))}
              </span>
              <ChevronDown className={cn(
                'w-3.5 h-3.5 flex-shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180',
                'text-[#1ed760]'
              )} />
            </>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" sideOffset={6} className={variant === 'sidebar' ? 'w-52' : 'w-40'}>
        {/* Organizations list */}
        {allOrganizations.map((org) => {
          const isSelected = currentOrganization?.id === org.id;
          return (
            <DropdownMenuItem
              key={org.id}
              className="cursor-pointer flex items-center justify-between py-2"
              onClick={() => handleSelectOrganization(org)}
            >
              <span className="text-sm font-medium text-white truncate">{getOrgDisplayName(org)}</span>
              {isSelected && <Check className="w-4 h-4 text-[#1ed760] flex-shrink-0" />}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}