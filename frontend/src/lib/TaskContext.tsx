'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { taskAPI } from './api';
import websocketService from './websocket';

// Define task status types
export enum TaskStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELED = 'CANCELED'
}

// Task interface
export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at?: string;
  updated_at?: string;
  error?: string;
  progress?: number;
  result?: any;
}

// Context interface
interface TaskContextValue {
  tasks: Record<string, Task>;
  createTask: (title: string, description: string, options?: any) => Promise<Task>;
  cancelTask: (taskId: string) => Promise<void>;
  getTask: (taskId: string) => Task | null;
  isLoading: boolean;
  error: string | null;
}

// Default context value
const defaultValue: TaskContextValue = {
  tasks: {},
  createTask: async () => ({ id: '', title: '', description: '', status: 'pending' }),
  cancelTask: async () => {},
  getTask: () => null,
  isLoading: false,
  error: null,
};

// Create context
const TaskContext = createContext<TaskContextValue>(defaultValue);

// Use Tasks hook
export const useTasks = () => useContext(TaskContext);

// TaskProvider props
interface TaskProviderProps {
  children: React.ReactNode;
}

// TaskProvider Component
export const TaskProvider: React.FC<TaskProviderProps> = ({ children }) => {
  const [tasks, setTasks] = useState<Record<string, Task>>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [subscriptions, setSubscriptions] = useState<Record<string, () => void>>({});

  // Handle task updates
  const handleTaskUpdate = useCallback((taskId: string, data: any) => {
    setTasks(prevTasks => ({
      ...prevTasks,
      [taskId]: {
        ...prevTasks[taskId],
        ...data,
      },
    }));
  }, []);

  // Subscribe to task updates
  const subscribeToTask = useCallback((taskId: string) => {
    // Skip if we already have a subscription for this task
    if (subscriptions[taskId]) return;

    try {
      // Subscribe to WebSocket updates
      const unsubscribe = websocketService.subscribeToTask(taskId, (data) => {
        handleTaskUpdate(taskId, data);
      });

      // Store the unsubscribe function
      setSubscriptions(prev => ({
        ...prev,
        [taskId]: unsubscribe,
      }));
    } catch (err) {
      console.warn('Failed to subscribe to task updates:', err);
      // Continue execution even if subscription fails
    }
  }, [subscriptions, handleTaskUpdate]);

  // Unsubscribe from task updates
  const unsubscribeFromTask = useCallback((taskId: string) => {
    if (subscriptions[taskId]) {
      try {
        // Call the unsubscribe function
        subscriptions[taskId]();
        
        // Remove from subscriptions
        setSubscriptions(prev => {
          const newSubscriptions = { ...prev };
          delete newSubscriptions[taskId];
          return newSubscriptions;
        });
      } catch (err) {
        console.warn('Error unsubscribing from task:', err);
      }
    }
  }, [subscriptions]);

  // Connect/disconnect WebSocket
  useEffect(() => {
    try {
      // Attempt to connect to WebSocket
      websocketService.connect();
    } catch (err) {
      console.warn('WebSocket connection error:', err);
      // Don't set error state - application should continue without WebSocket
    }

    // Cleanup on unmount
    return () => {
      // Unsubscribe from all tasks
      Object.keys(subscriptions).forEach(taskId => {
        try {
          subscriptions[taskId]();
        } catch (err) {
          console.warn(`Error unsubscribing from task ${taskId}:`, err);
        }
      });

      try {
        // Disconnect WebSocket
        websocketService.disconnect();
      } catch (err) {
        console.warn('Error disconnecting WebSocket:', err);
      }
    };
  }, [subscriptions]);

  // Create task function
  const createTask = useCallback(async (title: string, description: string, options?: any): Promise<Task> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Implementation for task creation
      // This would typically call an API endpoint
      const taskId = `task-${Date.now()}`;
      
      const newTask: Task = {
        id: taskId,
        title,
        description,
        status: 'pending',
        created_at: new Date().toISOString(),
        ...options,
      };
      
      // Store the task locally
      setTasks(prevTasks => ({
        ...prevTasks,
        [taskId]: newTask,
      }));
      
      // Subscribe to updates for this task
      subscribeToTask(taskId);
      
      setIsLoading(false);
      return newTask;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      setError(errorMessage);
      setIsLoading(false);
      throw err;
    }
  }, [subscribeToTask]);

  // Cancel task function
  const cancelTask = useCallback(async (taskId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Update task status locally (optimistic update)
      setTasks(prevTasks => ({
        ...prevTasks,
        [taskId]: {
          ...prevTasks[taskId],
          status: 'failed',
          error: 'Task cancelled by user',
        },
      }));
      
      // Unsubscribe from the task
      unsubscribeFromTask(taskId);
      
      setIsLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel task';
      setError(errorMessage);
      setIsLoading(false);
      throw err;
    }
  }, [unsubscribeFromTask]);

  // Get task function
  const getTask = useCallback((taskId: string): Task | null => {
    return tasks[taskId] || null;
  }, [tasks]);

  // Context value
  const value: TaskContextValue = {
    tasks,
    createTask,
    cancelTask,
    getTask,
    isLoading,
    error,
  };

  return (
    <TaskContext.Provider value={value}>
      {children}
    </TaskContext.Provider>
  );
};

export default TaskContext;

// No need to re-export what's already exported
// export type { Task };
// export { TaskStatus }; 