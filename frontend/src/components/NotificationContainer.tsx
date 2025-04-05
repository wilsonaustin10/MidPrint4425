'use client'

import React, { createContext, useContext, useState, useCallback } from 'react';
import TaskNotification from './TaskNotification';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  title?: string;
  duration?: number;
}

interface NotificationContextType {
  showNotification: (type: 'success' | 'error' | 'info' | 'warning', message: string, title?: string, duration?: number) => void;
  clearNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const showNotification = useCallback(
    (type: 'success' | 'error' | 'info' | 'warning', message: string, title?: string, duration = 5000) => {
      const id = Math.random().toString(36).substring(2, 9);
      setNotifications(prev => [...prev, { id, type, message, title, duration }]);
    },
    []
  );

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  return (
    <NotificationContext.Provider value={{ showNotification, clearNotifications }}>
      {children}
      <div className="fixed z-50 top-0 right-0 p-4 space-y-4 pointer-events-none">
        {notifications.map(notification => (
          <TaskNotification
            key={notification.id}
            type={notification.type}
            message={notification.message}
            title={notification.title}
            duration={notification.duration}
            onClose={() => removeNotification(notification.id)}
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export default NotificationProvider; 