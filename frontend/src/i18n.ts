/**
 * Internationalization (i18n) configuration
 */

export const locales = ['zh-CN', 'en'] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'zh-CN';

/**
 * Detect browser language and return supported locale
 */
export function detectBrowserLanguage(): Locale {
  if (typeof window === 'undefined') return defaultLocale;

  const browserLang = navigator.language;
  const browserLocale = browserLang.toLowerCase();

  // Check for exact match
  if (locales.some((l) => l.toLowerCase() === browserLocale)) {
    return browserLocale as Locale;
  }

  // Check for language prefix match (e.g., 'zh' matches 'zh-CN')
  const langPrefix = browserLang.split('-')[0];
  for (const locale of locales) {
    if (locale.toLowerCase().startsWith(langPrefix)) {
      return locale;
    }
  }

  return defaultLocale;
}

/**
 * Locale display names in their respective languages
 */
export const localeNames: Record<Locale, string> = {
  'zh-CN': '中文',
  en: 'English',
};

/**
 * Date format options for different locales
 */
export const getDateFormatOptions = (locale: Locale): Intl.DateTimeFormatOptions => ({
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
});

/**
 * Format date string according to locale
 */
export function formatLocaleDate(date: Date | string, locale: Locale): string {
  return new Date(date).toLocaleString(locale, getDateFormatOptions(locale));
}
