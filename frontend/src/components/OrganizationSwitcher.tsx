'use client';

import { useEffect, useState } from 'react';
import { Building2, Plus, ChevronDown } from 'lucide-react';
import { useAuthStore, type Organization } from '@/lib/store';
import { organizationAPI } from '@/lib/services';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface MyOrganizations {
  owned: Organization[];
  joined: Organization[];
}

export function OrganizationSwitcher() {
  const { currentOrganization, setCurrentOrganization, setShowCreateOrganizationDialog, isAuthenticated, setMyOrganizations } = useAuthStore();
  const [organizations, setOrganizations] = useState<MyOrganizations>({ owned: [], joined: [] });
  const [loading, setLoading] = useState(false);

  // Load user's organizations when authenticated
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

  const handleCreateOrganization = () => {
    setShowCreateOrganizationDialog(true);
  };

  const allOrganizations = [...organizations.owned, ...organizations.joined];
  const displayName = currentOrganization ? currentOrganization.name : '工区';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="gap-2 rounded-xl border-2 border-indigo-200 bg-gradient-to-r from-indigo-100 to-indigo-50 shadow-sm hover:shadow-md"
          style={{
            boxShadow: "0 2px 0 rgba(79, 70, 229, 0.15), 0 4px 8px rgba(79, 70, 229, 0.1)"
          }}
        >
          <Building2 className="h-4 w-4 text-indigo-600" />
          <span className="text-sm font-medium text-gray-700">{displayName}</span>
          <ChevronDown className="h-4 w-4 text-gray-500" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {/* Public workspace */}
        <DropdownMenuItem
          className={cn(
            "cursor-pointer",
            !currentOrganization && "bg-indigo-50"
          )}
          onClick={() => handleSelectOrganization(null)}
        >
          <Building2 className="mr-2 h-4 w-4" />
          工区
        </DropdownMenuItem>

        {/* User's organizations */}
        {allOrganizations.length > 0 && (
          <>
            <DropdownMenuSeparator />
            {allOrganizations.map((org) => (
              <DropdownMenuItem
                key={org.id}
                className={cn(
                  "cursor-pointer",
                  currentOrganization?.id === org.id && "bg-indigo-50"
                )}
                onClick={() => handleSelectOrganization(org)}
              >
                <Building2 className="mr-2 h-4 w-4" />
                {org.name}
              </DropdownMenuItem>
            ))}
          </>
        )}

        <DropdownMenuSeparator />
        {/* Create organization button */}
        <DropdownMenuItem
          className="cursor-pointer text-indigo-600 focus:text-indigo-600"
          onClick={handleCreateOrganization}
        >
          <Plus className="mr-2 h-4 w-4" />
          创建私服
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}