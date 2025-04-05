'use client';

import { TaskProvider } from './TaskContext';
import { NotificationProvider } from '@/components/NotificationContainer';
import { SessionProvider } from './SessionContext';

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <TaskProvider>
        <NotificationProvider>
          {children}
        </NotificationProvider>
      </TaskProvider>
    </SessionProvider>
  );
} 