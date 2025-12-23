import { useState, useEffect, useCallback } from 'react';
import { gamificationApi } from '@/lib/api';
import type {
  UserGamificationProfile,
  ModuleStatus,
  GamificationDashboard,
  GamificationPreferences,
  EnableGamificationRequest,
  DisableGamificationRequest,
  FinancialEvent,
  GamificationResult,
  DataRetentionPolicy
} from '@/types/gamification';

export interface UseGamificationReturn {
  profile: UserGamificationProfile | null;
  status: ModuleStatus | null;
  dashboard: GamificationDashboard | null;
  loading: boolean;
  error: string | null;
  isEnabled: boolean;
  canShowGamification: boolean;
  enable: (request: EnableGamificationRequest) => Promise<void>;
  disable: (request: DisableGamificationRequest) => Promise<void>;
  updatePreferences: (preferences: GamificationPreferences) => Promise<void>;
  processEvent: (event: FinancialEvent) => Promise<GamificationResult | null>;
  refresh: () => Promise<void>;
}

export function useGamification(): UseGamificationReturn {
  const [profile, setProfile] = useState<UserGamificationProfile | null>(null);
  const [status, setStatus] = useState<ModuleStatus | null>(null);
  const [dashboard, setDashboard] = useState<GamificationDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isEnabled = status?.enabled ?? false;
  const canShowGamification = isEnabled && profile?.module_enabled === true;

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Always fetch status first
      const statusData = await gamificationApi.getStatus();
      setStatus(statusData);

      if (statusData.enabled) {
        // If enabled, fetch profile and dashboard
        const [profileData, dashboardData] = await Promise.all([
          gamificationApi.getProfile(),
          gamificationApi.getDashboard()
        ]);
        
        setProfile(profileData);
        setDashboard(dashboardData);
      } else {
        // If disabled, clear profile and dashboard
        setProfile(null);
        setDashboard(null);
      }
    } catch (err) {
      console.error('Error fetching gamification data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load gamification data');
    } finally {
      setLoading(false);
    }
  }, []);

  const enable = useCallback(async (request: EnableGamificationRequest) => {
    try {
      setLoading(true);
      setError(null);
      
      const newProfile = await gamificationApi.enable(request);
      setProfile(newProfile);
      
      // Refresh all data after enabling
      await fetchData();
    } catch (err) {
      console.error('Error enabling gamification:', err);
      setError(err instanceof Error ? err.message : 'Failed to enable gamification');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchData]);

  const disable = useCallback(async (request: DisableGamificationRequest) => {
    try {
      setLoading(true);
      setError(null);
      
      await gamificationApi.disable(request);
      
      // Clear local state
      setProfile(null);
      setDashboard(null);
      
      // Refresh status
      await fetchData();
    } catch (err) {
      console.error('Error disabling gamification:', err);
      setError(err instanceof Error ? err.message : 'Failed to disable gamification');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchData]);

  const updatePreferences = useCallback(async (preferences: GamificationPreferences) => {
    try {
      setError(null);
      
      const updatedProfile = await gamificationApi.updatePreferences(preferences);
      setProfile(updatedProfile);
      
      // Refresh dashboard to reflect preference changes
      const dashboardData = await gamificationApi.getDashboard();
      setDashboard(dashboardData);
    } catch (err) {
      console.error('Error updating preferences:', err);
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      throw err;
    }
  }, []);

  const processEvent = useCallback(async (event: FinancialEvent): Promise<GamificationResult | null> => {
    try {
      const response = await gamificationApi.processEvent(event);
      
      if (response.success && response.result) {
        // Refresh dashboard to show updated progress
        await fetchData();
        return response.result;
      }
      
      return null;
    } catch (err) {
      console.error('Error processing financial event:', err);
      // Don't throw here as this is often called in background
      return null;
    }
  }, [fetchData]);

  const refresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    profile,
    status,
    dashboard,
    loading,
    error,
    isEnabled,
    canShowGamification,
    enable,
    disable,
    updatePreferences,
    processEvent,
    refresh
  };
}

// Helper hook for just checking if gamification is enabled
export function useGamificationEnabled(): boolean {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const checkEnabled = async () => {
      try {
        const status = await gamificationApi.getStatus();
        setEnabled(status.enabled);
      } catch (err) {
        console.error('Error checking gamification status:', err);
        setEnabled(false);
      }
    };

    checkEnabled();
  }, []);

  return enabled;
}