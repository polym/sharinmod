import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { detectBrowserLanguage, type Locale } from '@/i18n';

export interface User {
  id?: number;
  email: string;
  name?: string;
  bio?: string;
  avatar_url?: string;
  token_balance?: number;
  contributed_tokens?: number;
  consumed_tokens?: number;
  is_admin?: boolean;
  force_password_change?: boolean;
  is_disabled?: boolean;
  subscription_count?: number;
  active_subscription_count?: number;
  last_used_at?: string;
  created_at?: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface MyOrganizationsData {
  owned: Organization[];
  joined: Organization[];
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  showLoginDialog: boolean;
  showChangePasswordDialog: boolean;
  showResetPasswordDialog: boolean;
  showProfileDialog: boolean;
  showInviteDialog: boolean;
  resetPasswordToken: string | null;
  redirectAfterLogin: string | null;
  _isLoggingOut: boolean; // Internal flag to prevent 401 race conditions
  // Organization state
  currentOrganization: Organization | null; // null = 公区
  myOrganizations: MyOrganizationsData | null; // cached org membership data
  showCreateOrganizationDialog: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
  setShowLoginDialog: (show: boolean) => void;
  setShowChangePasswordDialog: (show: boolean) => void;
  setShowResetPasswordDialog: (show: boolean, token?: string) => void;
  setShowProfileDialog: (show: boolean) => void;
  setShowInviteDialog: (show: boolean) => void;
  setRedirectAfterLogin: (path: string | null) => void;
  setCurrentOrganization: (org: Organization | null) => void;
  setMyOrganizations: (data: MyOrganizationsData | null) => void;
  setShowCreateOrganizationDialog: (show: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      showLoginDialog: false,
      showChangePasswordDialog: false,
      showResetPasswordDialog: false,
      showProfileDialog: false,
      showInviteDialog: false,
      resetPasswordToken: null,
      redirectAfterLogin: null,
      _isLoggingOut: false,
      currentOrganization: null,
      myOrganizations: null,
      showCreateOrganizationDialog: false,
      login: (user: User, token: string) => {
        set({ isAuthenticated: true, user, token, _isLoggingOut: false });
      },
      logout: () => {
        set({ isAuthenticated: false, user: null, token: null, _isLoggingOut: true, currentOrganization: null, myOrganizations: null });
      },
      updateUser: (user: User) => {
        set({ user });
      },
      setShowLoginDialog: (show: boolean) => {
        // 当打开登录对话框时，保存当前路径用于登录后跳转
        if (show && typeof window !== 'undefined') {
          const currentPath = window.location.pathname;
          // 排除首页和登录相关页面
          if (currentPath !== '/' && !currentPath.startsWith('/auth/')) {
            set({ showLoginDialog: show, redirectAfterLogin: currentPath });
            return;
          }
        }
        set({ showLoginDialog: show });
      },
      setShowChangePasswordDialog: (show: boolean) => {
        set({ showChangePasswordDialog: show });
      },
      setShowProfileDialog: (show: boolean) => {
        set({ showProfileDialog: show });
      },
      setShowInviteDialog: (show: boolean) => {
        set({ showInviteDialog: show });
      },
      setShowResetPasswordDialog: (show: boolean, token?: string) => {
        set({ showResetPasswordDialog: show, resetPasswordToken: token || null });
      },
      setRedirectAfterLogin: (path: string | null) => {
        set({ redirectAfterLogin: path });
      },
      setCurrentOrganization: (org: Organization | null) => {
        set({ currentOrganization: org });
      },
      setMyOrganizations: (data: MyOrganizationsData | null) => {
        set({ myOrganizations: data });
      },
      setShowCreateOrganizationDialog: (show: boolean) => {
        set({ showCreateOrganizationDialog: show });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
        currentOrganization: state.currentOrganization,
        // showLoginDialog, showChangePasswordDialog, showResetPasswordDialog, showProfileDialog, showInviteDialog, redirectAfterLogin, _isLoggingOut and showCreateOrganizationDialog are NOT persisted
      }),
    }
  )
);

// Locale state for i18n
interface LocaleState {
  locale: Locale | undefined;
  setLocale: (locale: Locale) => void;
}

// Normalize locale to proper case (zh-CN, en)
function normalizeLocale(loc: string | null): Locale | undefined {
  if (!loc) return undefined;
  if (loc.toLowerCase() === 'zh-cn' || loc.toLowerCase() === 'zh') return 'zh-CN';
  if (loc.toLowerCase() === 'en') return 'en';
  return 'zh-CN';
}

// Initial value is handled by Zustand persist middleware
// It will be undefined initially until hydration completes
export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      locale: undefined as Locale | undefined, // Will be filled after hydration
      setLocale: (locale: Locale) => set({ locale }),
    }),
    {
      name: 'sharinmod-locale',
      onRehydrateStorage: () => (state) => {
        // After hydration, if no locale was persisted, use browser language
        if (state && state.locale === undefined) {
          // Check localStorage directly and normalize
          const stored = localStorage.getItem('sharinmod-locale');
          if (stored) {
            try {
              const parsed = JSON.parse(stored);
              if (parsed.state && parsed.state.locale) {
                state.setLocale(normalizeLocale(parsed.state.locale) || 'zh-CN');
                return;
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
          state.setLocale(detectBrowserLanguage());
        }
      },
    }
  )
);
