import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';

/**
 * Interface for locale-aware formatting functions
 * Provides methods to format dates, currency, numbers, and percentages
 * according to the user's current locale
 */
export interface LocaleFormatter {
  /**
   * Format a date according to the current locale
   * @param date - The date to format
   * @param format - Optional format style ('short', 'medium', 'long', 'full')
   * @returns Formatted date string
   */
  formatDate(date: Date, format?: 'short' | 'medium' | 'long' | 'full'): string;

  /**
   * Format a currency amount according to the current locale
   * @param amount - The numeric amount to format
   * @param currency - Optional currency code (e.g., 'USD', 'EUR'). Defaults to 'USD'
   * @returns Formatted currency string
   */
  formatCurrency(amount: number, currency?: string): string;

  /**
   * Format a decimal number according to the current locale
   * @param value - The numeric value to format
   * @param decimals - Optional number of decimal places to display
   * @returns Formatted number string
   */
  formatNumber(value: number, decimals?: number): string;

  /**
   * Format a percentage according to the current locale
   * @param value - The numeric value (0-100 or 0-1) to format as percentage
   * @param decimals - Optional number of decimal places to display
   * @returns Formatted percentage string
   */
  formatPercent(value: number, decimals?: number): string;
}

/**
 * Hook that provides locale-aware formatting functions
 * Uses the current i18n locale to determine formatting rules
 * Caches formatter instances for performance
 *
 * @returns LocaleFormatter object with formatting methods
 *
 * @example
 * const formatter = useLocaleFormatter();
 * const formattedDate = formatter.formatDate(new Date());
 * const formattedCurrency = formatter.formatCurrency(1234.56, 'USD');
 */
export const useLocaleFormatter = (): LocaleFormatter => {
  const { i18n } = useTranslation();

  return useMemo(() => {
    const locale = i18n.language;

    // Map format styles to Intl.DateTimeFormat options
    const dateFormatOptions: Record<string, Intl.DateTimeFormatOptions> = {
      short: { year: 'numeric', month: '2-digit', day: '2-digit' },
      medium: { year: 'numeric', month: 'short', day: 'numeric' },
      long: { year: 'numeric', month: 'long', day: 'numeric' },
      full: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' },
    };

    return {
      formatDate: (date: Date, format: 'short' | 'medium' | 'long' | 'full' = 'medium'): string => {
        try {
          const options = dateFormatOptions[format];
          return new Intl.DateTimeFormat(locale, options).format(date);
        } catch (error) {
          console.error('Error formatting date:', error);
          try {
            return date.toISOString().split('T')[0];
          } catch {
            return 'Invalid Date';
          }
        }
      },

      formatCurrency: (amount: number, currency: string = 'USD'): string => {
        try {
          return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }).format(amount);
        } catch (error) {
          console.error('Error formatting currency:', error);
          return `${currency} ${amount.toFixed(2)}`;
        }
      },

      formatNumber: (value: number, decimals?: number): string => {
        try {
          const options: Intl.NumberFormatOptions = {
            minimumFractionDigits: decimals ?? 0,
            maximumFractionDigits: decimals ?? 20,
          };
          return new Intl.NumberFormat(locale, options).format(value);
        } catch (error) {
          console.error('Error formatting number:', error);
          return value.toString();
        }
      },

      formatPercent: (value: number, decimals: number = 2): string => {
        try {
          // Only multiply by 100 if value is in 0-1 range
          const percentValue = value <= 1 ? value : value / 100;
          return new Intl.NumberFormat(locale, {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
          }).format(percentValue);
        } catch (error) {
          console.error('Error formatting percent:', error);
          return `${value.toFixed(decimals)}%`;
        }
      },
    };
  }, [i18n.language]);
};
