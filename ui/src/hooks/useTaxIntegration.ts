import { useState, useEffect } from 'react';
import { api, TaxIntegrationStatus } from '@/lib/api';

export function useTaxIntegration() {
  const [status, setStatus] = useState<TaxIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkTaxIntegrationStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get<TaxIntegrationStatus>('/tax-integration/status');
        setStatus(response);
      } catch (err) {
        console.error('Error checking tax integration status:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setStatus({
          enabled: false,
          configured: false,
          connection_tested: false,
        });
      } finally {
        setLoading(false);
      }
    };

    checkTaxIntegrationStatus();
  }, []);

  const isEnabled = status ? status.enabled && status.configured : false;

  return {
    status,
    loading,
    error,
    isEnabled,
    refetch: () => {
      // Re-run the effect by updating a dependency
      setStatus(null);
      setLoading(true);
      setError(null);
    },
  };
}