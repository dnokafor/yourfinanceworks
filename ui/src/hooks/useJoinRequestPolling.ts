import { useEffect, useRef } from 'react';
import { apiRequest } from '@/lib/api';

interface JoinRequest {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  status: string;
  created_at: string;
}

const POLL_INTERVAL = 60000; // Poll every 60 seconds
const SEEN_REQUESTS_KEY = 'seen_join_requests';

export function useJoinRequestPolling(
  isAdmin: boolean,
  addNotification: (type: 'join_request', title: string, message: string, actionUrl?: string) => string
) {
  const seenRequestsRef = useRef<Set<number>>(new Set());
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load seen requests from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SEEN_REQUESTS_KEY);
      if (stored) {
        seenRequestsRef.current = new Set(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Failed to load seen join requests:', error);
    }
  }, []);

  // Save seen requests to localStorage
  const saveSeenRequests = () => {
    try {
      localStorage.setItem(
        SEEN_REQUESTS_KEY,
        JSON.stringify(Array.from(seenRequestsRef.current))
      );
    } catch (error) {
      console.error('Failed to save seen join requests:', error);
    }
  };

  const checkForNewRequests = async () => {
    if (!isAdmin) return;

    try {
      const requests = await apiRequest<JoinRequest[]>('/organization-join/pending');
      
      // Filter for new pending requests
      const newRequests = requests.filter(
        req => req.status === 'pending' && !seenRequestsRef.current.has(req.id)
      );

      // Create reminder notifications for new requests (handled by backend)
      // No need to add to bottom notification bell anymore

      // Mark as seen
      newRequests.forEach(req => {
        seenRequestsRef.current.add(req.id);
      });

      if (newRequests.length > 0) {
        saveSeenRequests();
      }
    } catch (error) {
      console.error('Failed to check for join requests:', error);
    }
  };

  useEffect(() => {
    if (!isAdmin) return;

    // Initial check
    checkForNewRequests();

    // Set up polling
    pollIntervalRef.current = setInterval(checkForNewRequests, POLL_INTERVAL);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [isAdmin, addNotification]);

  return {
    checkForNewRequests,
  };
}
