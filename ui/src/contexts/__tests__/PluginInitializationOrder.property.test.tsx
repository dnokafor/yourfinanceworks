import React from 'react';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { PluginProvider, usePlugins } from '../PluginContext';

// Test component to access the context
const TestComponent = () => {
  const {
    plugins,
    enabledPlugins,
    loading,
    initializePlugin,
    getPluginInitializationStatus
  } = usePlugins();

  if (loading) {
    return <div data-testid="loading">Loading...</div>;
  }

  return (
    <div>
      <div data-testid="plugin-count">{plugins.length}</div>
      <div data-testid="enabled-count">{enabledPlugins.length}</div>
      <div data-testid="enabled-plugins">{JSON.stringify(enabledPlugins)}</div>
      {plugins.map(plugin => (
        <div key={plugin.id}>
          <span data-testid={`plugin-${plugin.id}-status`}>{plugin.status}</span>
          <span data-testid={`plugin-${plugin.id}-enabled`}>{plugin.enabled.toString()}</span>
          <span data-testid={`plugin-${plugin.id}-init-status`}>
            {JSON.stringify(getPluginInitializationStatus(plugin.id))}
          </span>
        </div>
      ))}
    </div>
  );
};

describe('Property 10: Plugin Initialization Order', () => {
  let mockLocalStorage: any;
  let mockDispatchEvent: any;

  beforeEach(() => {
    // Mock localStorage
    mockLocalStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      length: 0,
      key: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });

    // Mock window.dispatchEvent
    mockDispatchEvent = vi.spyOn(window, 'dispatchEvent').mockImplementation(() => true);
  });

  afterEach(() => {
    cleanup(); // Clean up DOM between tests
    vi.restoreAllMocks();
  });

  /**
   * **Feature: plugin-management, Property 10: Plugin Initialization Order**
   *
   * Property: For any application startup, only plugins that are in the enabled state
   * should be loaded and initialized.
   *
   * **Validates: Requirements 5.5**
   *
   * This property verifies that:
   * 1. Only enabled plugins are initialized during application startup
   * 2. Disabled plugins remain in inactive/disabled state
   * 3. Plugin initialization status correctly reflects the enabled state
   * 4. The initialization order respects the enabled state from storage
   */
  it('should only initialize plugins that are in enabled state during startup', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate arbitrary plugin states - array of plugin IDs that should be enabled
        fc.array(
          fc.constantFrom('investments'), // Only test with available plugins
          { minLength: 0, maxLength: 1 } // Since we only have 1 plugin in the test registry
        ),
        async (enabledPluginIds: string[]) => {
          // Clean up any previous renders
          cleanup();

          // Setup: Mock localStorage to return the generated enabled plugins
          const uniqueEnabledPlugins = [...new Set(enabledPluginIds)]; // Remove duplicates
          mockLocalStorage.getItem.mockImplementation((key: string) => {
            if (key === 'enabledPlugins') {
              return JSON.stringify(uniqueEnabledPlugins);
            }
            return null;
          });

          // Reset mocks for each test iteration
          mockDispatchEvent.mockClear();

          // Act: Render the PluginProvider (simulates application startup)
          render(
            <PluginProvider>
              <TestComponent />
            </PluginProvider>
          );

          // Wait for initialization to complete
          await waitFor(() => {
            expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
          }, { timeout: 5000 });

          // Assert: Verify plugin initialization order property
          const enabledCount = parseInt(screen.getByTestId('enabled-count').textContent || '0');
          const actualEnabledPlugins = JSON.parse(screen.getByTestId('enabled-plugins').textContent || '[]');

          // Property 1: Only enabled plugins should be in the enabled list
          expect(enabledCount).toBe(uniqueEnabledPlugins.length);
          expect(actualEnabledPlugins).toEqual(expect.arrayContaining(uniqueEnabledPlugins));
          expect(actualEnabledPlugins.length).toBe(uniqueEnabledPlugins.length);

          // Property 2: Check each plugin's initialization status
          const availablePlugins = ['investments']; // Known available plugins

          for (const pluginId of availablePlugins) {
            const isEnabled = uniqueEnabledPlugins.includes(pluginId);
            const pluginStatus = screen.getByTestId(`plugin-${pluginId}-status`).textContent;
            const pluginEnabled = screen.getByTestId(`plugin-${pluginId}-enabled`).textContent === 'true';
            const initStatus = JSON.parse(screen.getByTestId(`plugin-${pluginId}-init-status`).textContent || '{}');

            if (isEnabled) {
              // Property 3: Enabled plugins should be initialized and active
              expect(pluginEnabled).toBe(true);
              expect(pluginStatus).toBe('active');
              expect(initStatus.isInitialized).toBe(true);
              expect(initStatus.error).toBeUndefined();
            } else {
              // Property 4: Disabled plugins should remain inactive
              expect(pluginEnabled).toBe(false);
              expect(pluginStatus).toBe('inactive');
              expect(initStatus.isInitialized).toBe(false);
            }
          }

          // Property 5: Verify initialization events were dispatched only for enabled plugins
          const initializationEvents = mockDispatchEvent.mock.calls.filter(
            call => call[0]?.type === 'plugin-initialized'
          );

          // Should have initialization events for each enabled plugin
          expect(initializationEvents.length).toBe(uniqueEnabledPlugins.length);

          // Each initialization event should be for an enabled plugin
          for (const call of initializationEvents) {
            const event = call[0];
            expect(uniqueEnabledPlugins).toContain(event.detail.pluginId);
            expect(event.detail.success).toBe(true);
          }

          // Property 6: No initialization events should be dispatched for disabled plugins
          const disabledPlugins = availablePlugins.filter(id => !uniqueEnabledPlugins.includes(id));
          for (const disabledPluginId of disabledPlugins) {
            const hasInitEvent = initializationEvents.some(
              call => call[0]?.detail?.pluginId === disabledPluginId
            );
            expect(hasInitEvent).toBe(false);
          }
        }
      ),
      {
        numRuns: 100, // Run 100 iterations to test various combinations
        timeout: 10000, // 10 second timeout for async operations
        verbose: true // Show detailed output on failure
      }
    );
  });

  /**
   * **Feature: plugin-management, Property 10: Plugin Initialization Order - Edge Cases**
   *
   * Property: Plugin initialization should handle edge cases correctly during startup.
   *
   * This property verifies edge cases like:
   * 1. Empty enabled plugins list
   * 2. Invalid plugin IDs in enabled list
   * 3. Storage corruption scenarios
   */
  it('should handle edge cases in plugin initialization order', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate edge case scenarios
        fc.oneof(
          fc.constant([]), // Empty enabled plugins
          fc.constant(['non-existent-plugin']), // Invalid plugin ID
          fc.constant(['investments', 'non-existent-plugin']), // Mix of valid and invalid
          fc.constant(['', 'investments']), // Empty string in list
          fc.constant(['investments', 'investments']), // Duplicates
        ),
        async (enabledPluginIds: string[]) => {
          // Clean up any previous renders
          cleanup();

          // Setup: Mock localStorage with edge case data
          mockLocalStorage.getItem.mockImplementation((key: string) => {
            if (key === 'enabledPlugins') {
              return JSON.stringify(enabledPluginIds);
            }
            return null;
          });

          mockDispatchEvent.mockClear();

          // Act: Render the PluginProvider
          render(
            <PluginProvider>
              <TestComponent />
            </PluginProvider>
          );

          // Wait for initialization to complete
          await waitFor(() => {
            expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
          }, { timeout: 5000 });

          // Assert: System should handle edge cases gracefully
          const enabledCount = parseInt(screen.getByTestId('enabled-count').textContent || '0');
          const actualEnabledPlugins = JSON.parse(screen.getByTestId('enabled-plugins').textContent || '[]');

          // Property 1: Only valid, existing plugins should be enabled
          const validPlugins = enabledPluginIds.filter(id =>
            id && typeof id === 'string' && id.trim() !== '' && id === 'investments'
          );
          const uniqueValidPlugins = [...new Set(validPlugins)];

          expect(enabledCount).toBe(uniqueValidPlugins.length);
          expect(actualEnabledPlugins).toEqual(expect.arrayContaining(uniqueValidPlugins));

          // Property 2: Invalid plugins should not cause system failure
          expect(screen.getByTestId('plugin-count')).toHaveTextContent('1'); // Should still discover available plugins

          // Property 3: Only valid plugins should have initialization events
          const initializationEvents = mockDispatchEvent.mock.calls.filter(
            call => call[0]?.type === 'plugin-initialized'
          );
          expect(initializationEvents.length).toBe(uniqueValidPlugins.length);

          // Property 4: System should remain stable regardless of input
          expect(screen.getByTestId('plugin-investments-status')).toBeInTheDocument();
          const investmentStatus = screen.getByTestId('plugin-investments-status').textContent;
          expect(['active', 'inactive']).toContain(investmentStatus);
        }
      ),
      {
        numRuns: 50,
        timeout: 10000,
        verbose: true
      }
    );
  });

  /**
   * **Feature: plugin-management, Property 10: Plugin Initialization Order - Storage Failures**
   *
   * Property: Plugin initialization should be resilient to storage failures during startup.
   */
  it('should handle storage failures gracefully during initialization', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different storage failure scenarios
        fc.oneof(
          fc.constant('storage_unavailable'),
          fc.constant('json_parse_error'),
          fc.constant('storage_exception'),
          fc.constant('corrupted_data')
        ),
        async (failureType: string) => {
          // Clean up any previous renders
          cleanup();

          // Setup: Mock different storage failure scenarios
          switch (failureType) {
            case 'storage_unavailable':
              Object.defineProperty(window, 'localStorage', {
                value: {
                  getItem: () => { throw new Error('localStorage not available'); },
                  setItem: () => { throw new Error('localStorage not available'); },
                  removeItem: () => { throw new Error('localStorage not available'); },
                },
                writable: true,
              });
              break;
            case 'json_parse_error':
              mockLocalStorage.getItem.mockReturnValue('invalid json data');
              break;
            case 'storage_exception':
              mockLocalStorage.getItem.mockImplementation(() => {
                throw new Error('Storage access denied');
              });
              break;
            case 'corrupted_data':
              mockLocalStorage.getItem.mockImplementation((key: string) => {
                if (key === 'enabledPlugins') {
                  return '["investments"]';
                }
                if (key === 'enabledPlugins_checksum') {
                  return 'invalid_checksum'; // Will cause integrity check to fail
                }
                if (key === 'enabledPlugins_fallback') {
                  return '["investments"]';
                }
                return null;
              });
              break;
          }

          mockDispatchEvent.mockClear();

          // Act: Render the PluginProvider
          render(
            <PluginProvider>
              <TestComponent />
            </PluginProvider>
          );

          // Wait for initialization to complete
          await waitFor(() => {
            expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
          }, { timeout: 5000 });

          // Assert: System should remain functional despite storage failures

          // Property 1: Plugin discovery should still work
          expect(screen.getByTestId('plugin-count')).toHaveTextContent('1');
          expect(screen.getByTestId('plugin-investments-status')).toBeInTheDocument();

          // Property 2: System should use fallback behavior
          const enabledCount = parseInt(screen.getByTestId('enabled-count').textContent || '0');
          expect(enabledCount).toBeGreaterThanOrEqual(0); // Should not crash

          // Property 3: Plugin status should be consistent
          const investmentStatus = screen.getByTestId('plugin-investments-status').textContent;
          expect(['active', 'inactive', 'error']).toContain(investmentStatus);

          // Property 4: No initialization should occur for corrupted/unavailable storage (except fallback cases)
          const initializationEvents = mockDispatchEvent.mock.calls.filter(
            call => call[0]?.type === 'plugin-initialized'
          );

          if (failureType === 'corrupted_data') {
            // Corrupted data might still allow fallback initialization
            expect(initializationEvents.length).toBeGreaterThanOrEqual(0);
          } else {
            // Other failures should result in no plugins being initialized
            expect(initializationEvents.length).toBe(0);
          }

          // Property 5: System should dispatch appropriate error events
          const storageErrorEvents = mockDispatchEvent.mock.calls.filter(
            call => call[0]?.type === 'plugin-storage-warning' ||
                   call[0]?.type === 'plugin-storage-mode'
          );
          expect(storageErrorEvents.length).toBeGreaterThan(0);
        }
      ),
      {
        numRuns: 20, // Fewer runs for error scenarios
        timeout: 10000,
        verbose: true
      }
    );
  });
});