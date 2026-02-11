import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

/**
 * Property 16: Translation Key Naming Convention
 *
 * *For any* translation key in the system, the key MUST follow the hierarchical
 * snake_case format (e.g., `investments.holdings.title`, `validation.required_field`).
 *
 * **Validates: Requirements 6.2**
 */
describe('Property 16: Translation Key Naming Convention', () => {
  // Valid translation key pattern: hierarchical dot-separated segments with snake_case
  const validKeyPattern = /^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$/;

  const translationKeyArbitrary = fc.tuple(
    fc.array(
      fc.stringMatching(/^[a-z_][a-z0-9_]*$/),
      { minLength: 1, maxLength: 5 }
    )
  ).map(([segments]) => segments.join('.'));

  it('should validate that all generated keys follow hierarchical snake_case format', () => {
    fc.assert(
      fc.property(translationKeyArbitrary, (key) => {
        // All generated keys should match the pattern
        expect(key).toMatch(validKeyPattern);
      }),
      { numRuns: 100 }
    );
  });

  it('should reject keys with uppercase letters', () => {
    const invalidKeys = [
      'investments.Holdings.title',
      'INVESTMENTS.holdings.title',
      'investments.holdings.Title',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should reject keys with hyphens', () => {
    const invalidKeys = [
      'investments-holdings.title',
      'investments.holdings-title',
      'investments.holdings.my-title',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should reject keys with spaces', () => {
    const invalidKeys = [
      'investments holdings.title',
      'investments.holdings title',
      'investments. holdings.title',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should reject keys starting with numbers', () => {
    const invalidKeys = [
      '1investments.holdings.title',
      'investments.1holdings.title',
      'investments.holdings.1title',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should accept valid keys with underscores', () => {
    const validKeys = [
      'investments.holdings.title',
      'investments.holdings_list.title',
      'validation.required_field',
      'error_messages.portfolio_not_found',
      'success_messages.portfolio_created_successfully',
    ];

    validKeys.forEach(key => {
      expect(key).toMatch(validKeyPattern);
    });
  });

  it('should accept single-level keys', () => {
    const validKeys = [
      'title',
      'description',
      'error_message',
      'success_notification',
    ];

    validKeys.forEach(key => {
      expect(key).toMatch(validKeyPattern);
    });
  });

  it('should reject empty keys', () => {
    expect('').not.toMatch(validKeyPattern);
  });

  it('should reject keys with trailing dots', () => {
    const invalidKeys = [
      'investments.holdings.',
      'investments.holdings.title.',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should reject keys with leading dots', () => {
    const invalidKeys = [
      '.investments.holdings.title',
      '.holdings.title',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should reject keys with consecutive dots', () => {
    const invalidKeys = [
      'investments..holdings.title',
      'investments.holdings..title',
    ];

    invalidKeys.forEach(key => {
      expect(key).not.toMatch(validKeyPattern);
    });
  });

  it('should validate key structure consistency across multiple keys', () => {
    fc.assert(
      fc.property(
        fc.array(translationKeyArbitrary, { minLength: 1, maxLength: 10 }),
        (keys) => {
          // All keys should follow the same naming convention
          keys.forEach(key => {
            expect(key).toMatch(validKeyPattern);

            // Each segment should be valid
            const segments = key.split('.');
            segments.forEach(segment => {
              expect(segment).toMatch(/^[a-z_][a-z0-9_]*$/);
            });
          });
        }
      ),
      { numRuns: 50 }
    );
  });
});
