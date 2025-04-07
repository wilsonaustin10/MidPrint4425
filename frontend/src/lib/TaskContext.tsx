'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { taskAPI, agentAPI } from './api';
import websocketService, { WebSocketMessage } from './websocket';

// Task status types
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

// Task interface
export interface Task {
  id: string;
  status: TaskStatus;
  prompt: string;
  result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
  screenshot_data?: string;
  page_state?: any;
}

// TaskContextValue interface
interface TaskContextValue {
  tasks: Task[];
  currentTask: Task | null;
  isLoading: boolean;
  isConnected: boolean;
  createTask: (title: string, prompt: string) => Promise<Task>;
  selectTask: (taskId: string) => void;
  clearCurrentTask: () => void;
  getTaskById: (taskId: string) => Task | undefined;
  refreshTasks: () => Promise<void>;
  updateLocalTask: (taskId: string, updates: Partial<Task>) => void;
}

// Create the context
const TaskContext = createContext<TaskContextValue | undefined>(undefined);

// Provider component
export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const websocketSubscriptions = useRef<(() => void)[]>([]);
  const websocketConnectionCheck = useRef<NodeJS.Timeout | null>(null);

  // Function to refresh tasks from the API
  const refreshTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      const fetchedTasks = await taskAPI.getTasks();
      setTasks(fetchedTasks);
      
      // If we have a current task, update it with the latest data
      if (currentTask) {
        const updatedCurrentTask = fetchedTasks.find((t: Task) => t.id === currentTask.id);
        if (updatedCurrentTask) {
          setCurrentTask(updatedCurrentTask);
        }
      }
    } catch (error) {
      console.error('Error refreshing tasks:', error);
    } finally {
      setIsLoading(false);
    }
  }, [currentTask]);

  // Function to get a task by ID
  const getTaskById = useCallback((taskId: string) => {
    return tasks.find(task => task.id === taskId);
  }, [tasks]);

  // Function to select a task as the current one
  const selectTask = useCallback((taskId: string) => {
    const task = tasks.find(task => task.id === taskId);
    if (task) {
      setCurrentTask(task);
    } else {
      console.warn(`Task with ID ${taskId} not found`);
    }
  }, [tasks]);

  // Function to clear the current task
  const clearCurrentTask = useCallback(() => {
    setCurrentTask(null);
  }, []);

  // Function to update a task locally without API call
  const updateLocalTask = useCallback((taskId: string, updates: Partial<Task>) => {
    setTasks(prevTasks => {
      const updatedTasks = prevTasks.map(task => {
        if (task.id === taskId) {
          return { ...task, ...updates };
        }
        return task;
      });
      return updatedTasks;
    });

    // Also update current task if it's the one being updated
    if (currentTask && currentTask.id === taskId) {
      setCurrentTask(prevTask => {
        if (prevTask) {
          return { ...prevTask, ...updates };
        }
        return prevTask;
      });
    }
  }, [currentTask]);

  // Function to create a new task
  const createTask = useCallback(async (title: string, prompt: string) => {
    const taskId = uuidv4(); // Generate a client-side ID
    const timestamp = new Date().toISOString();
    
    // Create a temporary task object to show in the UI immediately
    const newTask: Task = {
      id: taskId,
      status: 'pending',
      prompt,
      created_at: timestamp,
      updated_at: timestamp,
    };
    
    setTasks(prevTasks => [newTask, ...prevTasks]);
    setCurrentTask(newTask);
    
    try {
      // Use the agent API to execute the task
      const response = await agentAPI.executeTask(prompt);
      
      // Get the real task ID from the response
      const realTaskId = response.task_id;
      
      if (!realTaskId) {
        throw new Error('No task ID returned from the API');
      }
      
      // Get the task details
      const createdTask = await taskAPI.getTask(realTaskId);
      
      // Update local state with the server response
      setTasks(prevTasks => {
        // Remove the temporary task
        const filteredTasks = prevTasks.filter(t => t.id !== taskId);
        // Add the real task
        return [createdTask, ...filteredTasks];
      });
      
      // Update current task if it's the one we just created
      if (currentTask && currentTask.id === taskId) {
        setCurrentTask(createdTask);
      }
      
      return createdTask;
    } catch (error) {
      console.error('Error creating task:', error);
      
      // Update the task status to failed
      updateLocalTask(taskId, { 
        status: 'failed', 
        error: error instanceof Error ? error.message : 'Unknown error creating task'
      });
      
      throw error;
    }
  }, [currentTask, updateLocalTask]);

  // Handle WebSocket connection status
  useEffect(() => {
    // Check connection status periodically
    websocketConnectionCheck.current = setInterval(() => {
      setIsConnected(websocketService.isConnected());
    }, 2000);

    // Initialize the connection
    websocketService.connect();

    // Add global message handler
    const unsubscribe = websocketService.addMessageHandler((message: WebSocketMessage) => {
      if (message.type === 'connection_established') {
        setIsConnected(true);
      }
    });

    // Cleanup function
    return () => {
      if (websocketConnectionCheck.current) {
        clearInterval(websocketConnectionCheck.current);
      }
      unsubscribe();
    };
  }, []);

  // Load tasks on component mount
  useEffect(() => {
    refreshTasks();
  }, [refreshTasks]);

  // Add WebSocket subscription for a task when it becomes the current task
  useEffect(() => {
    // Clean up previous subscriptions
    websocketSubscriptions.current.forEach(unsubscribe => unsubscribe());
    websocketSubscriptions.current = [];

    // If we have a current task, subscribe to updates
    if (currentTask) {
      console.log(`Subscribing to updates for task ${currentTask.id}`);
      
      const unsubscribe = websocketService.subscribeToTask(
        currentTask.id,
        (data) => {
          console.log(`Received update for task ${currentTask.id}:`, data);
          
          // Handle different types of updates
          if (data.status) {
            updateLocalTask(currentTask.id, { status: data.status });
          }
          
          if (data.result) {
            updateLocalTask(currentTask.id, { result: data.result });
          }
          
          if (data.screenshot) {
            updateLocalTask(currentTask.id, { screenshot_data: data.screenshot });
          }
          
          if (data.page_state) {
            updateLocalTask(currentTask.id, { page_state: data.page_state });
          }
          
          if (data.error) {
            updateLocalTask(currentTask.id, { 
              error: data.error,
              status: 'failed'
            });
          }
        }
      );
      
      websocketSubscriptions.current.push(unsubscribe);
    }
    
    // Cleanup function
    return () => {
      websocketSubscriptions.current.forEach(unsubscribe => unsubscribe());
      websocketSubscriptions.current = [];
    };
  }, [currentTask, updateLocalTask]);

  const value = {
    tasks,
    currentTask,
    isLoading,
    isConnected,
    createTask,
    selectTask,
    clearCurrentTask,
    getTaskById,
    refreshTasks,
    updateLocalTask,
  };

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
};

// Custom hook to use the task context
export const useTaskContext = (): TaskContextValue => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTaskContext must be used within a TaskProvider');
  }
  return context;
};

// No need to re-export what's already exported
// export type { Task };
// export { TaskStatus }; 