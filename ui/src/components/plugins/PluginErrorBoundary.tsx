import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface Props {
  children: ReactNode;
  pluginId?: string;
  pluginName?: string;
  fallbackComponent?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

/**
 * Error boundary specifically designed for plugin components
 * Provides graceful fallback UI and error reporting for plugin failures
 */
export class PluginErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error for debugging
    console.error('Plugin Error Boundary caught an error:', error, errorInfo);

    // Update state with error info
    this.setState({
      error,
      errorInfo
    });

    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Dispatch a global event for error tracking
    window.dispatchEvent(new CustomEvent('plugin-component-error', {
      detail: {
        pluginId: this.props.pluginId,
        pluginName: this.props.pluginName,
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      }
    }));

    // If this is a plugin-specific error, try to disable the plugin
    if (this.props.pluginId) {
      window.dispatchEvent(new CustomEvent('plugin-error-disable', {
        detail: {
          pluginId: this.props.pluginId,
          reason: `Component error: ${error.message}`
        }
      }));
    }
  }

  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // If a custom fallback component is provided, use it
      if (this.props.fallbackComponent) {
        return this.props.fallbackComponent;
      }

      // Default fallback UI
      const { pluginName, pluginId } = this.props;
      const { error, retryCount } = this.state;
      const canRetry = retryCount < this.maxRetries;

      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
                <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-lg">
                {pluginName ? `${pluginName} Error` : 'Plugin Error'}
              </CardTitle>
              <CardDescription>
                {pluginName
                  ? `The ${pluginName} plugin encountered an error and couldn't load properly.`
                  : 'A plugin component encountered an error and couldn\'t load properly.'
                }
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Error details */}
              {error && (
                <Alert variant="destructive">
                  <AlertDescription className="text-sm font-mono">
                    {error.message}
                  </AlertDescription>
                </Alert>
              )}

              {/* Retry information */}
              {retryCount > 0 && (
                <div className="text-sm text-muted-foreground text-center">
                  Retry attempt: {retryCount} of {this.maxRetries}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex flex-col gap-2">
                {canRetry && (
                  <Button
                    onClick={this.handleRetry}
                    variant="default"
                    className="w-full"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Try Again
                  </Button>
                )}

                <Button
                  onClick={this.handleReset}
                  variant="outline"
                  className="w-full"
                >
                  Reset Component
                </Button>

                <Button
                  onClick={this.handleGoHome}
                  variant="ghost"
                  className="w-full"
                >
                  <Home className="mr-2 h-4 w-4" />
                  Go to Dashboard
                </Button>
              </div>

              {/* Plugin-specific information */}
              {pluginId && (
                <div className="text-xs text-muted-foreground text-center pt-2 border-t">
                  Plugin ID: {pluginId}
                  {retryCount >= this.maxRetries && (
                    <div className="mt-1 text-red-600 dark:text-red-400">
                      Maximum retry attempts reached. The plugin may be disabled.
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component that wraps a plugin component with error boundary
 */
export function withPluginErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  pluginId: string,
  pluginName: string,
  fallbackComponent?: ReactNode
) {
  const WithErrorBoundary = (props: P) => (
    <PluginErrorBoundary
      pluginId={pluginId}
      pluginName={pluginName}
      fallbackComponent={fallbackComponent}
    >
      <WrappedComponent {...props} />
    </PluginErrorBoundary>
  );

  WithErrorBoundary.displayName = `withPluginErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithErrorBoundary;
}

/**
 * Lightweight error boundary for plugin menu items in sidebar
 */
export const PluginMenuErrorBoundary: React.FC<{
  children: ReactNode;
  pluginId: string;
  pluginName: string;
}> = ({ children, pluginId, pluginName }) => {
  return (
    <PluginErrorBoundary
      pluginId={pluginId}
      pluginName={pluginName}
      fallbackComponent={
        <div className="mx-2 rounded-xl p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm font-medium">{pluginName} Error</span>
          </div>
          <div className="text-xs text-red-600 dark:text-red-400 mt-1">
            Plugin failed to load
          </div>
        </div>
      }
    >
      {children}
    </PluginErrorBoundary>
  );
};