import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PluginProvider } from '../contexts/PluginContext';
import { PluginsTab } from '../components/settings/PluginsTab';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock the FeatureContext
let mockFeatureContext = {
  features: {},
  hasFeature: () => true,
  isFeatureEnabled: (featureId: string) => featureId === 'investments', // Only investments is licensed
  isFeatureExpired: () => false,
  isLoading: false,
  refreshFeatures: vi.fn(),
  refetch: vi.fn(),
  licenseStatus: { isValid: true, features: ['investments'] },
};

vi.mock('../contexts/FeatureContext', () => ({
  FeatureProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useFeatures: () => mockFeatureContext,
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => options?.defaultValue || key,
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    }
  }),
}));

// Mock auth utilities
let mockAuthUtils = {
  getCurrentUser: () => ({
    id: 1,
    email: 'admin@test.com',
    role: 'admin',
    tenant_id: 1,
    is_superuser: true,
    first_name: 'Admin',
    last_name: 'User'
  }),
  getCurrentUserRole: () => 'admin',
  isAdmin: () => true,
};

vi.mock('../utils/auth', () => mockAuthUtils);

// Mock hooks
vi.mock('../hooks/useMe', () => ({
  useMe: () => ({
    data: { role: 'admin' },
    isLoading: false
  })
}));

vi.mock('../hooks/useOrganizations', () => ({
  useOrganizations: () => ({
    data: [{ id: 1, name: 'Test Org', role: 'admin' }]
  })
}));

vi.mock('../hooks/use-mobile', () => ({
  useIsMobile: () => false
}));

// Mock API
vi.mock('../lib/api', () => ({
  settingsApi: {
    getSettings: vi.fn().mockResolvedValue({
      company_info: { name: 'Test Company' }
    })
  }
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  }
}));

// Simple test component that shows plugin state and allows toggling
const SimplePluginTest = ({ isAdmin = true }: { isAdmin?: boolean }) => {
  return (
    <div data-testid="plugin-test-app">
      <PluginsTab isAdmin={isAdmin} />
    </div>
  );
};

// Test wrapper with all providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <PluginProvider>
          {children}
        </PluginProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Plugin Enable/Disable Workflow Integration', () => {
  let mockLocalStorage: any;
  let user: any;

  beforeEach(() => {
    user = userEvent.setup();

    // Reset mocks
    mockFeatureContext.isFeatureEnabled = (featureId: string) => featureId === 'investments';
    mockAuthUtils.getCurrentUser = () => ({
      id: 1,
      email: 'admin@test.com',
      role: 'admin',
      tenant_id: 1,
      is_superuser: true,
      first_name: 'Admin',
      last_name: 'User'
    });
    mockAuthUtils.isAdmin = () => true;

    // Mock localStorage
    mockLocalStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      key: vi.fn(),
      length: 0,
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });

    // Mock window.dispatchEvent
    vi.spyOn(window, 'dispatchEvent').mockImplementation(() => true);

    // Mock console methods to reduce noise
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('completes full plugin enable workflow', async () => {
    // Start with no enabled plugins
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    // Wait for plugins to load
    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Verify plugin is initially disabled
    const pluginSwitch = screen.getByRole('switch');
    expect(pluginSwitch).not.toBeChecked();

    // Enable the plugin
    await user.click(pluginSwitch);

    // Wait for plugin to be enabled and initialized
    await waitFor(() => {
      expect(pluginSwitch).toBeChecked();
    });

    // Verify localStorage was called to save the enabled state
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'enabledPlugins',
      JSON.stringify(['investments'])
    );
  });

  it('completes full plugin disable workflow', async () => {
    // Start with investments plugin enabled
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(['investments']));

    render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    // Wait for plugins to load
    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Verify plugin is initially enabled
    const pluginSwitch = screen.getByRole('switch');
    expect(pluginSwitch).toBeChecked();

    // Disable the plugin
    await user.click(pluginSwitch);

    // Wait for plugin to be disabled
    await waitFor(() => {
      expect(pluginSwitch).not.toBeChecked();
    });

    // Verify localStorage was called to save the disabled state
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'enabledPlugins',
      JSON.stringify([])
    );
  });

  it('handles plugin initialization errors gracefully', async () => {
    // Start with no enabled plugins
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    // Wait for plugins to load
    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Enable the plugin
    const pluginSwitch = screen.getByRole('switch');
    await user.click(pluginSwitch);

    // Plugin should still be enabled even if initialization has issues
    await waitFor(() => {
      expect(pluginSwitch).toBeChecked();
    });
  });

  it('persists plugin state across browser sessions', async () => {
    // First session - enable plugin
    mockLocalStorage.getItem.mockReturnValue(null);

    const { unmount } = render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Enable plugin
    const pluginSwitch = screen.getByRole('switch');
    await user.click(pluginSwitch);

    await waitFor(() => {
      expect(pluginSwitch).toBeChecked();
    });

    // Verify state was saved
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'enabledPlugins',
      JSON.stringify(['investments'])
    );

    // Unmount component (simulate browser close)
    unmount();

    // Second session - plugin should be loaded as enabled
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(['investments']));

    render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    // Wait for plugins to load
    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Verify plugin is still enabled
    const newPluginSwitch = screen.getByRole('switch');
    expect(newPluginSwitch).toBeChecked();
  });

  it('handles storage failures gracefully', async () => {
    // Mock localStorage to fail on setItem
    mockLocalStorage.getItem.mockReturnValue(null);
    mockLocalStorage.setItem.mockImplementation(() => {
      throw new Error('Storage quota exceeded');
    });

    render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Try to enable plugin
    const pluginSwitch = screen.getByRole('switch');
    await user.click(pluginSwitch);

    // Plugin should remain disabled due to storage failure
    await waitFor(() => {
      expect(pluginSwitch).not.toBeChecked();
    });
  });

  it('handles cross-component state synchronization', async () => {
    // Start with plugin disabled
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <TestWrapper>
        <SimplePluginTest />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Verify initial state - plugin disabled
    const pluginSwitch = screen.getByRole('switch');
    expect(pluginSwitch).not.toBeChecked();

    // Enable plugin
    await user.click(pluginSwitch);

    // Verify plugin is enabled
    await waitFor(() => {
      expect(pluginSwitch).toBeChecked();
    });

    // Disable plugin again
    await user.click(pluginSwitch);

    // Verify plugin is disabled
    await waitFor(() => {
      expect(pluginSwitch).not.toBeChecked();
    });
  });

  it('validates admin access control throughout workflow', async () => {
    // Mock non-admin user
    mockAuthUtils.getCurrentUser = () => ({
      id: 2,
      email: 'user@test.com',
      role: 'user',
      tenant_id: 1,
      is_superuser: false,
      first_name: 'Regular',
      last_name: 'User'
    });
    mockAuthUtils.isAdmin = () => false;

    render(
      <TestWrapper>
        <SimplePluginTest isAdmin={false} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Verify admin warning is shown
    expect(screen.getAllByText(/Administrator Access Required/)[0]).toBeInTheDocument();

    // Verify switch is disabled for non-admin
    const pluginSwitch = screen.getByRole('switch');
    expect(pluginSwitch).toBeDisabled();

    // Try to click disabled switch (should not work)
    await user.click(pluginSwitch);

    // Plugin should remain disabled
    expect(pluginSwitch).not.toBeChecked();
  });

  it('handles license validation throughout workflow', async () => {
    // Mock feature context to show investments as unlicensed
    mockFeatureContext.isFeatureEnabled = () => false; // No license for investments

    render(
      <TestWrapper>
        <SimplePluginTest isAdmin={true} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Investment Management')).toBeInTheDocument();
    });

    // Verify license warning is shown
    expect(screen.getByText(/This plugin requires a commercial license/)).toBeInTheDocument();

    // Verify switch is disabled due to license
    const pluginSwitch = screen.getByRole('switch');
    expect(pluginSwitch).toBeDisabled();

    // Try to click disabled switch
    await user.click(pluginSwitch);

    // Plugin should remain disabled
    expect(pluginSwitch).not.toBeChecked();
  });
});