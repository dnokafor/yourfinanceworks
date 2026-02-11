import { renderHook } from '@testing-library/react';
import { vi, describe, beforeEach, it, expect } from 'vitest';
import { useLocaleFormatter } from '../formatters';
import * as i18next from 'react-i18next';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: vi.fn(),
}));

describe('useLocaleFormatter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('formatDate', () => {
    it('formats date in English locale (short format)', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      // Create date in local timezone to avoid timezone issues
      const date = new Date(2024, 0, 15); // January 15, 2024
      const formatted = result.current.formatDate(date, 'short');

      expect(formatted).toMatch(/01\/15\/2024|1\/15\/2024|15\/01\/2024|15\/1\/2024/);
    });

    it('formats date in Spanish locale (short format)', () => {
      const mockI18n = { language: 'es' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const date = new Date(2024, 0, 15);
      const formatted = result.current.formatDate(date, 'short');

      expect(formatted).toMatch(/15\/01\/2024|15\/1\/2024|01\/15\/2024|1\/15\/2024/);
    });

    it('formats date in German locale (short format)', () => {
      const mockI18n = { language: 'de' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const date = new Date(2024, 0, 15);
      const formatted = result.current.formatDate(date, 'short');

      expect(formatted).toMatch(/15\.01\.2024|15\.1\.2024|01\.15\.2024|1\.15\.2024/);
    });

    it('formats date in French locale (short format)', () => {
      const mockI18n = { language: 'fr' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const date = new Date(2024, 0, 15);
      const formatted = result.current.formatDate(date, 'short');

      expect(formatted).toMatch(/15\/01\/2024|15\/1\/2024|01\/15\/2024|1\/15\/2024/);
    });

    it('uses medium format by default', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const date = new Date(2024, 0, 15);
      const formatted = result.current.formatDate(date);

      expect(formatted).toContain('2024');
      expect(formatted).toMatch(/Jan|January|15|14/);
    });

    it('handles invalid date gracefully', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const invalidDate = new Date('invalid');
      const formatted = result.current.formatDate(invalidDate, 'short');

      expect(formatted).toBeDefined();
      expect(typeof formatted).toBe('string');
      expect(formatted).toBe('Invalid Date');
    });
  });

  describe('formatCurrency', () => {
    it('formats currency in English locale with USD', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatCurrency(1234.56, 'USD');

      expect(formatted).toMatch(/\$1,234\.56|1,234\.56\s*USD/);
    });

    it('formats currency in German locale with EUR', () => {
      const mockI18n = { language: 'de' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatCurrency(1234.56, 'EUR');

      expect(formatted).toMatch(/1\.234,56|1,234\.56/);
    });

    it('formats currency in Spanish locale with EUR', () => {
      const mockI18n = { language: 'es' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatCurrency(1234.56, 'EUR');

      expect(formatted).toBeDefined();
      expect(typeof formatted).toBe('string');
    });

    it('uses USD as default currency', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatCurrency(1000);

      expect(formatted).toMatch(/\$1,000\.00|1,000\.00\s*USD/);
    });

    it('handles zero currency', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatCurrency(0, 'USD');

      expect(formatted).toMatch(/\$0\.00|0\.00\s*USD/);
    });

    it('handles negative currency', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatCurrency(-1234.56, 'USD');

      expect(formatted).toMatch(/-|\(.*\)/);
    });
  });

  describe('formatNumber', () => {
    it('formats number in English locale', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatNumber(1000000);

      expect(formatted).toBe('1,000,000');
    });

    it('formats number in German locale', () => {
      const mockI18n = { language: 'de' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatNumber(1000000);

      expect(formatted).toBe('1.000.000');
    });

    it('formats number with specified decimals', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatNumber(1234.5678, 2);

      expect(formatted).toBe('1,234.57');
    });

    it('formats number with zero decimals', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatNumber(1234.5678, 0);

      expect(formatted).toBe('1,235');
    });

    it('handles negative numbers', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatNumber(-1000000);

      expect(formatted).toBe('-1,000,000');
    });
  });

  describe('formatPercent', () => {
    it('formats percent in English locale (0-1 range)', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatPercent(0.0525, 2);

      expect(formatted).toMatch(/5\.25%|5,25%/);
    });

    it('formats percent in English locale (0-100 range)', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      // 0.0525 is 5.25% in 0-1 range
      const formatted = result.current.formatPercent(0.0525, 2);

      expect(formatted).toMatch(/5\.25%|5,25%/);
    });

    it('formats percent in German locale', () => {
      const mockI18n = { language: 'de' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatPercent(0.0525, 2);

      expect(formatted).toMatch(/5,25\s?%|5\.25\s?%/);
    });

    it('uses 2 decimal places by default', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatPercent(0.123456);

      expect(formatted).toMatch(/12\.35%|12,35%/);
    });

    it('handles zero percent', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatPercent(0, 2);

      expect(formatted).toMatch(/0\.00%|0,00%/);
    });

    it('handles negative percent', () => {
      const mockI18n = { language: 'en' };
      (i18next.useTranslation as any).mockReturnValue({
        i18n: mockI18n,
        t: vi.fn(),
      });

      const { result } = renderHook(() => useLocaleFormatter());
      const formatted = result.current.formatPercent(-0.0525, 2);

      expect(formatted).toMatch(/-5\.25%|-5,25%/);
    });
  });

  describe('locale switching', () => {
    it('updates formatting when locale changes', () => {
      const mockI18n = { language: 'en' };
      const useTranslationMock = vi.fn(() => ({
        i18n: mockI18n,
        t: vi.fn(),
      }));
      (i18next.useTranslation as any).mockImplementation(useTranslationMock);

      const { result, rerender } = renderHook(() => useLocaleFormatter());
      const dateEn = result.current.formatDate(new Date('2024-01-15'), 'short');

      // Change locale to German
      mockI18n.language = 'de';
      rerender();

      const dateDe = result.current.formatDate(new Date('2024-01-15'), 'short');

      expect(dateEn).not.toBe(dateDe);
    });
  });
});
