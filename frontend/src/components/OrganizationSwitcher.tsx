'use client';

import { useEffect, useState } from 'react';
import { Globe, Lock, Plus, ChevronDown, Check } from 'lucide-react';
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

interface MyOrganizations {
  owned: Organization[];
  joined: Organization[];
}

export function OrganizationSwitcher() {
  const { currentOrganization, setCurrentOrganization, setShowCreateOrganizationDialog, isAuthenticated, setMyOrganizations } = useAuthStore();
  const [organizations, setOrganizations] = useState<MyOrganizations>({ owned: [], joined: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadOrganizations();
    }
  }, [isAuthenticated]);

  const loadOrganizations = async () => {
    setLoading(true);
    try {
      const response = await organizationAPI.getMyOrganizations();
      setOrganizations(response.data);
      setMyOrganizations(response.data);
    } catch (error) {
      console.error('[OrganizationSwitcher] Failed to load organizations:', error);
    } finally {
      setLoading(false);
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
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border-2 transition-all duration-200 cursor-pointer group',
            isPublic
              ? 'bg-gradient-to-r from-indigo-50 to-indigo-100/60 border-indigo-200 hover:border-indigo-300 hover:shadow-sm'
              : 'bg-gradient-to-r from-violet-50 to-violet-100/60 border-violet-200 hover:border-violet-300 hover:shadow-sm'
          )}
          style={{
            boxShadow: isPublic
              ? '0 1px 0 rgba(79,70,229,0.1), 0 2px 6px rgba(79,70,229,0.08)'
              : '0 1px 0 rgba(139,92,246,0.1), 0 2px 6px rgba(139,92,246,0.08)',
          }}
        >
          {/* Icon */}
          <div
            className={cn(
              'w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 border',
              isPublic
                ? 'bg-gradient-to-br from-indigo-500 to-indigo-600 border-indigo-400'
                : 'bg-gradient-to-br from-violet-500 to-violet-600 border-violet-400'
            )}
            style={{
              boxShadow: isPublic
                ? '0 2px 0 rgba(79,70,229,0.3)'
                : '0 2px 0 rgba(139,92,246,0.3)',
            }}
          >
            {isPublic
              ? <Globe className="w-3.5 h-3.5 text-white" />
              : <Lock className="w-3.5 h-3.5 text-white" />
            }
          </div>

          {/* Text */}
          <div className="flex-1 text-left min-w-0">
            <div className="text-xs font-medium text-gray-400 leading-none mb-0.5">
              {isPublic ? '公共空间' : '私服'}
            </div>
            <div className={cn(
              'text-sm font-semibold truncate leading-none',
              isPublic ? 'text-indigo-700' : 'text-violet-700'
            )}>
              {isPublic ? '公区' : currentOrganization?.name}
            </div>
          </div>

          {/* Chevron */}
          <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" sideOffset={6} className="w-52">
        {/* Public workspace */}
        <DropdownMenuItem
          className="cursor-pointer flex items-center gap-2.5 py-2"
          onClick={() => handleSelectOrganization(null)}
        >
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
            <Globe className="w-3 h-3 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-800">公区</div>
            <div className="text-xs text-gray-400">公共共享空间</div>
          </div>
          {isPublic && <Check className="w-4 h-4 text-indigo-500 flex-shrink-0" />}
        </DropdownMenuItem>

        {/* Private organizations */}
        {allOrganizations.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <div className="px-2 py-1">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">私服</span>
            </div>
            {allOrganizations.map((org) => {
              const isSelected = currentOrganization?.id === org.id;
              return (
                <DropdownMenuItem
                  key={org.id}
                  className="cursor-pointer flex items-center gap-2.5 py-2"
                  onClick={() => handleSelectOrganization(org)}
                >
                  <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center flex-shrink-0">
                    <Lock className="w-3 h-3 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate">{org.name}</div>
                    <div className="text-xs text-gray-400">
                      {organizations.owned.some(o => o.id === org.id) ? '创建者' : '成员'}
                    </div>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-violet-500 flex-shrink-0" />}
                </DropdownMenuItem>
              );
            })}
          </>
        )}

        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="cursor-pointer flex items-center gap-2 py-2 text-indigo-600 focus:text-indigo-600"
          onClick={() => setShowCreateOrganizationDialog(true)}
        >
          <div className="w-6 h-6 rounded-md border-2 border-dashed border-indigo-300 flex items-center justify-center flex-shrink-0">
            <Plus className="w-3 h-3 text-indigo-500" />
          </div>
          <span className="text-sm font-medium">创建私服</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}