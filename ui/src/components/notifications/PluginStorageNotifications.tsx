import React, { useEffect } from 'react';
import { useNotifications } from '@/hooks/useNotifications';

/**
 * Component that listens for plugin storage events and displays appropriate notifications
 * This ensures users are informed about storage issues and the application's fallback behavior
 */
export const PluginStorageNotifications: React.FC = () => {
  const { addNotification } = useNotifications();

  useEffect(() => {
    // Handle storage warnings (non-critical issues)
    const handleStorageWarnings = (event: CustomEvent) => {
      const { warnings } = event.detail;

      if (warnings && warnings.length > 0) {
        // Show a single notification for multiple warnings
        const warningMessage = warnings.length === 1
          ? warnings[0]
          : `${warnings.length} plugin storage warnings detected`;

        addNotification({
          type: 'warning',
          title: 'Plugin Storage Warning',
          message: warningMessage,
          duration: 8000, // Show longer for warnings
          actions: [
            {
              label: 'View Details',
              onClick: () => {
                console.log('Plugin storage warnings:', warnings);
                // Could open a detailed modal here
              }
            }
          ]
        });
      }
    };

    // Handle storage errors (critical issues)
    const handleStorageError = (event: CustomEvent) => {
      const { error, pluginId, enabled } = event.detail;

      const action = enabled ? 'enable' : 'disable';
      const message = pluginId
        ? `Failed to ${action} plugin "${pluginId}": ${error}`
        : `Plugin storage error: ${error}`;

      addNotification({
        type: 'error',
        title: 'Plugin Storage Error',
        message,
        duration: 12000, // Show longer for errors
        actions: [
          {
            label: 'Retry',
            onClick: () => {
              // Trigger a plugin context refresh
              window.dispatchEvent(new CustomEvent('plugin-storage-retry'));
            }
          }
        ]
      });
    };

    // Handle discovery warnings
    const handleDiscoveryWarnings = (event: CustomEvent) => {
      const { errors } = event.detail;

      if (errors && errors.length > 0) {
        addNotification({
          type: 'warning',
          title: 'Plugin Discovery Issues',
          message: `${errors.length} plugin(s) could not be loaded properly`,
          duration: 10000,
          actions: [
            {
              label: 'Refresh',
              onClick: () => {
                window.dispatchEvent(new CustomEvent('plugin-discovery-refresh'));
              }
            }
          ]
        });
      }
    };

    // Handle initialization failures
    const handleInitializationFailed = (event: CustomEvent) => {
      const { pluginId, error } = event.detail;

      addNotification({
        type: 'error',
        title: 'Plugin Initialization Failed',
        message: `Plugin "${pluginId}" failed to initialize: ${error}`,
        duration: 10000,
        actions: [
          {
            label: 'Retry',
            onClick: () => {
              window.dispatchEvent(new CustomEvent('plugin-retry-initialization', {
                detail: { pluginId }
              }));
            }
          }
        ]
      });
    };

    // Handle storage mode notifications (when falling back to in-memory)
    const handleStorageMode = (event: CustomEvent) => {
      const { mode, reason } = event.detail;

      if (mode === 'in-memory') {
        addNotification({
          type: 'info',
          title: 'Plugin Storage Mode',
          message: `Using in-memory storage: ${reason}. Plugin settings will not persist across sessions.`,
          duration: 15000,
          actions: [
            {
              label: 'Learn More',
              onClick: () => {
                // Could open help documentation
                console.log('Storage mode info:', { mode, reason });
              }
            }
          ]
        });
      }
    };

    // Handle plugin auto-disable notifications
    const handlePluginAutoDisabled = (event: CustomEvent) => {
      const { pluginId, reason } = event.detail;

      addNotification({
        type: 'warning',
        title: 'Plugin Automatically Disabled',
        message: `Plugin "${pluginId}" was disabled due to errors: ${reason}`,
        duration: 12000,
        actions: [
          {
            label: 'View Settings',
            onClick: () => {
              window.location.href = '/settings?tab=plugins';
            }
          }
        ]
      });
    };

    // Handle component error notifications
    const handleComponentError = (event: CustomEvent) => {
      const { pluginId, pluginName, error } = event.detail;

      addNotification({
        type: 'error',
        title: 'Plugin Component Error',
        message: `${pluginName || pluginId} component failed: ${error}`,
        duration: 10000,
        actions: [
          {
            label: 'Reload Page',
            onClick: () => {
              window.location.reload();
            }
          }
        ]
      });
    };

    // Handle route error notifications
    const handleRouteError = (event: CustomEvent) => {
      const { pluginId, pluginName, routePath, error } = event.detail;

      addNotification({
        type: 'error',
        title: 'Plugin Route Error',
        message: `${pluginName || pluginId} failed to load route ${routePath}: ${error}`,
        duration: 15000,
        actions: [
          {
            label: 'Go to Dashboard',
            onClick: () => {
              window.location.href = '/';
            }
          },
          {
            label: 'Plugin Settings',
            onClick: () => {
              window.location.href = '/settings?tab=plugins';
            }
          }
        ]
      });
    };

    // Add event listeners
    window.addEventListener('plugin-storage-warnings', handleStorageWarnings as EventListener);
    window.addEventListener('plugin-storage-error', handleStorageError as EventListener);
    window.addEventListener('plugin-discovery-warnings', handleDiscoveryWarnings as EventListener);
    window.addEventListener('plugin-initialization-failed', handleInitializationFailed as EventListener);
    window.addEventListener('plugin-storage-mode', handleStorageMode as EventListener);
    window.addEventListener('plugin-auto-disabled', handlePluginAutoDisabled as EventListener);
    window.addEventListener('plugin-component-error', handleComponentError as EventListener);
    window.addEventListener('plugin-route-error', handleRouteError as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('plugin-storage-warnings', handleStorageWarnings as EventListener);
      window.removeEventListener('plugin-storage-error', handleStorageError as EventListener);
      window.removeEventListener('plugin-discovery-warnings', handleDiscoveryWarnings as EventListener);
      window.removeEventListener('plugin-initialization-failed', handleInitializationFailed as EventListener);
      window.removeEventListener('plugin-storage-mode', handleStorageMode as EventListener);
      window.removeEventListener('plugin-auto-disabled', handlePluginAutoDisabled as EventListener);
      window.removeEventListener('plugin-component-error', handleComponentError as EventListener);
      window.removeEventListener('plugin-route-error', handleRouteError as EventListener);
    };
  }, [addNotification]);

  // This component doesn't render anything - it just handles notifications
  return null;
};