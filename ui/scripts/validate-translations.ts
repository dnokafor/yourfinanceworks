#!/usr/bin/env node

/**
 * Translation validation script
 * Validates that all translation keys exist in all supported locales
 * Usage: npx ts-node ui/scripts/validate-translations.ts
 */

import * as fs from 'fs';
import * as path from 'path';

interface ValidationResult {
  isValid: boolean;
  totalKeys: number;
  missingKeys: Record<string, string[]>;
  missingLocales: Record<string, string[]>;
  coverage: Record<string, number>;
  errors: string[];
}

const SUPPORTED_LOCALES = ['en', 'es', 'fr', 'de'];
const TRANSLATIONS_DIR = path.join(__dirname, '../src/i18n/plugins/investments');

/**
 * Flattens nested object into dot-notation keys
 */
function flattenKeys(obj: any, prefix = ''): Record<string, any> {
  const result: Record<string, any> = {};

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const value = obj[key];
      const newKey = prefix ? `${prefix}.${key}` : key;

      if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
        Object.assign(result, flattenKeys(value, newKey));
      } else {
        result[newKey] = value;
      }
    }
  }

  return result;
}

/**
 * Loads translation file for a locale
 */
function loadTranslations(locale: string): any {
  const filePath = path.join(TRANSLATIONS_DIR, `${locale}.json`);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Translation file not found: ${filePath}`);
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

/**
 * Validates all translation files
 */
function validateTranslations(): ValidationResult {
  const result: ValidationResult = {
    isValid: true,
    totalKeys: 0,
    missingKeys: {},
    missingLocales: {},
    coverage: {},
    errors: [],
  };

  try {
    // Load English translations as source of truth
    let enTranslations: any;
    try {
      enTranslations = loadTranslations('en');
    } catch (error) {
      result.errors.push(`Failed to load English translations: ${error}`);
      result.isValid = false;
      return result;
    }

    const enKeys = flattenKeys(enTranslations);
    result.totalKeys = Object.keys(enKeys).length;

    // Validate each locale
    for (const locale of SUPPORTED_LOCALES) {
      if (locale === 'en') {
        result.coverage['en'] = 100;
        continue;
      }

      let localeTranslations: any;
      try {
        localeTranslations = loadTranslations(locale);
      } catch (error) {
        result.errors.push(`Failed to load ${locale} translations: ${error}`);
        result.missingKeys[locale] = Object.keys(enKeys);
        result.coverage[locale] = 0;
        result.isValid = false;
        continue;
      }

      const localeKeys = flattenKeys(localeTranslations);
      const missing: string[] = [];

      // Find missing keys
      for (const key of Object.keys(enKeys)) {
        if (!(key in localeKeys)) {
          missing.push(key);
          if (!result.missingLocales[key]) {
            result.missingLocales[key] = [];
          }
          result.missingLocales[key].push(locale);
        }
      }

      if (missing.length > 0) {
        result.missingKeys[locale] = missing;
        result.isValid = false;
      }

      result.coverage[locale] = result.totalKeys > 0
        ? ((result.totalKeys - missing.length) / result.totalKeys) * 100
        : 100;
    }

    // Check for orphaned keys (keys in other locales but not in English)
    for (const locale of SUPPORTED_LOCALES) {
      if (locale === 'en') continue;

      try {
        const localeTranslations = loadTranslations(locale);
        const localeKeys = flattenKeys(localeTranslations);

        for (const key of Object.keys(localeKeys)) {
          if (!(key in enKeys)) {
            result.errors.push(
              `Orphaned key in ${locale}: "${key}" exists but not in English`
            );
            result.isValid = false;
          }
        }
      } catch (error) {
        // Already handled above
      }
    }
  } catch (error) {
    result.errors.push(`Unexpected error during validation: ${error}`);
    result.isValid = false;
  }

  return result;
}

/**
 * Formats and prints validation results
 */
function printResults(result: ValidationResult): void {
  console.log('\n=== Translation Validation Report ===\n');

  console.log(`Total Keys: ${result.totalKeys}`);
  console.log(`Status: ${result.isValid ? '✓ VALID' : '✗ INVALID'}\n`);

  console.log('Coverage by Locale:');
  for (const locale of SUPPORTED_LOCALES) {
    const coverage = result.coverage[locale] || 0;
    const status = coverage === 100 ? '✓' : '✗';
    console.log(`  ${status} ${locale.toUpperCase()}: ${coverage.toFixed(1)}%`);
  }

  if (Object.keys(result.missingKeys).length > 0) {
    console.log('\nMissing Keys by Locale:');
    for (const [locale, keys] of Object.entries(result.missingKeys)) {
      if (keys.length > 0) {
        console.log(`  ${locale.toUpperCase()}: ${keys.length} missing`);
        if (keys.length <= 10) {
          keys.forEach(key => console.log(`    - ${key}`));
        } else {
          keys.slice(0, 5).forEach(key => console.log(`    - ${key}`));
          console.log(`    ... and ${keys.length - 5} more`);
        }
      }
    }
  }

  if (Object.keys(result.missingLocales).length > 0) {
    console.log('\nKeys Missing from Locales:');
    const entries = Object.entries(result.missingLocales);
    if (entries.length <= 10) {
      entries.forEach(([key, locales]) => {
        console.log(`  ${key}: missing from ${locales.join(', ')}`);
      });
    } else {
      entries.slice(0, 5).forEach(([key, locales]) => {
        console.log(`  ${key}: missing from ${locales.join(', ')}`);
      });
      console.log(`  ... and ${entries.length - 5} more keys`);
    }
  }

  if (result.errors.length > 0) {
    console.log('\nErrors:');
    result.errors.forEach(error => console.log(`  ✗ ${error}`));
  }

  console.log('\n=====================================\n');
}

// Run validation
const result = validateTranslations();
printResults(result);

// Exit with appropriate code
process.exit(result.isValid ? 0 : 1);
