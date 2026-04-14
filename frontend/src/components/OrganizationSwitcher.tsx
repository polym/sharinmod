'use client';

import { useEffect, useState } from 'react';
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

interface MyOrganizations {
  owned: Organization[];
  joined: Organization[];
}

export function OrganizationSwitcher({ variant = 'header' }: { variant?: 'header' | 'sidebar' }) {
  const t = useTranslations('sidebar');
  const tCommon = useTranslations('common');
  const { currentOrganization, setCurrentOrganization, setShowCreateOrganizationDialog, isAuthenticated, setMyOrganizations } = useAuthStore();
  const [organizations, setOrganizations] = useState<MyOrganizations>({ owned: [], joined: [] });

  useEffect(() => {
    if (isAuthenticated) {
      loadOrganizations();
    }
  }, [isAuthenticated]);

  const loadOrganizations = async () => {
    try {
      const response = await organizationAPI.getMyOrganizations();
      setOrganizations(response.data);
      setMyOrganizations(response.data);
    } catch (error) {
      console.error('[OrganizationSwitcher] Failed to load organizations:', error);
    }
  };

  const handleSelectOrganization = (org: Organization | null) => {
    setCurrentOrganization(org);
  };

  const allOrganizations = [...organizations.owned, ...organizations.joined];
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