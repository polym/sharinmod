import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { detectBrowserLanguage, type Locale } from '@/i18n';

interface User {
  id?: number;
  email: string;
  name?: string;
  bio?: string;
  avatar_url?: string;
  token_balance?: number;
  contributed_tokens?: number;
  consumed_tokens?: number;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  showLoginDialog: boolean;
  showRegisterDialog: boolean;
  _isLoggingOut: boolean; // Internal flag to prevent 401 race conditions
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
  setShowLoginDialog: (show: boolean) => void;
  setShowRegisterDialog: (show: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      showLoginDialog: false,
      showRegisterDialog: false,
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
      setShowRegisterDialog: (show: boolean) => {
        set({ showRegisterDialog: show });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
        // showLoginDialog, showRegisterDialog and _isLoggingOut are NOT persisted
      }),
    }
  )
);

// Locale state for i18n
interface LocaleState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      locale: detectBrowserLanguage(),
      setLocale: (locale: Locale) => set({ locale }),
    }),
    {
      name: 'sharinmod-locale',
    }
  )
);
