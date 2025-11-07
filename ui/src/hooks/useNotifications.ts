import { useState, useCallback, useEffect } from 'react';
import { Notification } from '@/components/notifications/NotificationBell';

const MAX_NOTIFICATIONS = 50;

export function useNotifications() {
  // Notifications are now ephemeral - they don't persist across page reloads
  // This is the expected behavior for real-time notifications
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Clean up any old localStorage data from previous versions
  useEffect(() => {
    // Remove old notification storage if it exists
    localStorage.removeItem('ai_notifications');
    localStorage.removeItem('ai_notifications_version');
  }, []);

  const addNotification = useCallback((
    type: Notification['type'],
    title: string,
    message: string,
    actionUrl?: string
  ) => {
    const notification: Notification = {
      id: Date.now().toString(),
      type,
      title,
      message,
      timestamp: new Date(),
      read: false,
      actionUrl,
    };

    setNotifications(prev => [notification, ...prev].slice(0, MAX_NOTIFICATIONS));
    return notification.id;
  }, []);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const updateNotification = useCallback((id: string, updates: Partial<Notification>) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, ...updates } : n)
    );
  }, []);

  return {
    notifications,
    addNotification,
    markAsRead,
    clearAll,
    updateNotification,
  };
}