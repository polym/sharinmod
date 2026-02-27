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
  subscription_count?: number;
  active_subscription_count?: number;
  last_used_at?: string;
  created_at?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  showLoginDialog: boolean;
  _isLoggingOut: boolean; // Internal flag to prevent 401 race conditions
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
  setShowLoginDialog: (show: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      showLoginDialog: false,
      _isLoggingOut: false,
      login: (user: User, token: string) => {
        set({ isAuthenticated: true, user, token, _isLoggingOut: false });
      },
      logout: () => {
        set({ isAuthenticated: false, user: null, token: null, _isLoggingOut: true });
      },
      updateUser: (user: User) => {
        set({ user });
      },
      setShowLoginDialog: (show: boolean) => {
        set({ showLoginDialog: show });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
        // showLoginDialog and _isLoggingOut are NOT persisted
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
