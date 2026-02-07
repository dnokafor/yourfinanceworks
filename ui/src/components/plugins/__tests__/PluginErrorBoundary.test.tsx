import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { PluginErrorBoundary, PluginMenuErrorBoundary } from '../PluginErrorBoundary';

// Mock component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

describe('PluginErrorBoundary', () => {
  // Suppress console.error for these tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it('renders children when there is no error', () => {
    render(
      <PluginErrorBoundary pluginId="test-plugin" pluginName="Test Plugin">
        <ThrowError shouldThrow={false} />
      </PluginErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('renders error UI when child component throws', () => {
    render(
      <PluginErrorBoundary pluginId="test-plugin" pluginName="Test Plugin">
        <ThrowError shouldThrow={true} />
      </PluginErrorBoundary>
    );

    expect(screen.getByText('Test Plugin Error')).toBeInTheDocument();
    expect(screen.getByText(/The Test Plugin plugin encountered an error/)).toBeInTheDocument();
  });

  it('renders custom fallback component when provided', () => {
    const CustomFallback = <div>Custom error fallback</div>;

    render(
      <PluginErrorBoundary
        pluginId="test-plugin"
        pluginName="Test Plugin"
        fallbackComponent={CustomFallback}
      >
        <ThrowError shouldThrow={true} />
      </PluginErrorBoundary>
    );

    expect(screen.getByText('Custom error fallback')).toBeInTheDocument();
  });
});

describe('PluginMenuErrorBoundary', () => {
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it('renders children when there is no error', () => {
    render(
      <PluginMenuErrorBoundary pluginId="test-plugin" pluginName="Test Plugin">
        <div>Menu item content</div>
      </PluginMenuErrorBoundary>
    );

    expect(screen.getByText('Menu item content')).toBeInTheDocument();
  });

  it('renders compact error UI when child component throws', () => {
    render(
      <PluginMenuErrorBoundary pluginId="test-plugin" pluginName="Test Plugin">
        <ThrowError shouldThrow={true} />
      </PluginMenuErrorBoundary>
    );

    expect(screen.getByText('Test Plugin Error')).toBeInTheDocument();
    expect(screen.getByText('Plugin failed to load')).toBeInTheDocument();
  });
});