'use client';

import React, { useEffect, useState } from 'react';
import { useTaskContext, Task } from '@/lib/TaskContext';
import LoadingDots from './LoadingDots';
import MarkdownContent from './MarkdownContent';
import StatusMessage from './StatusMessage';

interface TaskViewProps {
  taskId?: string;
  className?: string;
}

export default function TaskView({ taskId, className = '' }: TaskViewProps) {
  const { getTaskById, currentTask, selectTask, isConnected } = useTaskContext();
  const [error, setError] = useState<string | null>(null);
  
  // Use the provided taskId or the current task
  useEffect(() => {
    if (taskId) {
      selectTask(taskId);
    }
  }, [taskId, selectTask]);
  
  // Get the task to display
  const task = taskId ? getTaskById(taskId) : currentTask;
  
  if (!task) {
    return (
      <div className={`flex flex-col items-center justify-center h-full p-4 ${className}`}>
        <StatusMessage type="info" message="No task selected" />
      </div>
    );
  }
  
  // Handle specific statuses
  const isLoading = task.status === 'pending' || task.status === 'in_progress';
  
  // Format the status for display
  const formatStatus = (status: string): string => {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };
  
  // Get the CSS class for the status badge
  const getStatusClasses = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`p-4 ${className}`}>
      <div className="mb-4">
        <div className="flex justify-between items-start">
          <h2 className="text-xl font-semibold">{task.prompt}</h2>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusClasses(task.status)}`}>
            {formatStatus(task.status)}
          </span>
        </div>
        <div className="text-sm text-gray-500 mt-1">
          Created: {new Date(task.created_at).toLocaleString()}
        </div>
      </div>
      
      {!isConnected && (
        <div className="mb-4">
          <StatusMessage 
            type="warning" 
            message="WebSocket connection lost. Reconnecting..." 
          />
        </div>
      )}
      
      {/* Display screenshots if available */}
      {task.screenshot_data && (
        <div className="mb-6">
          <h3 className="text-md font-medium mb-2">Current Browser View</h3>
          <div className="border rounded-md overflow-hidden">
            <img 
              src={`data:image/png;base64,${task.screenshot_data}`} 
              alt="Browser screenshot" 
              className="w-full h-auto"
            />
          </div>
        </div>
      )}
      
      {/* Display page state if available */}
      {task.page_state && (
        <div className="mb-6">
          <h3 className="text-md font-medium mb-2">Browser State</h3>
          <div className="bg-gray-50 rounded-md p-3 border">
            <div className="mb-2">
              <span className="font-medium">URL:</span>{' '}
              <span className="text-blue-600 truncate block">
                {task.page_state.url}
              </span>
            </div>
            {task.page_state.title && (
              <div className="mb-2">
                <span className="font-medium">Title:</span>{' '}
                <span>{task.page_state.title}</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Display result if available */}
      {task.result && (
        <div className="mb-6">
          <h3 className="text-md font-medium mb-2">Result</h3>
          <div className="bg-gray-50 rounded-md p-3 border">
            <MarkdownContent content={task.result} />
          </div>
        </div>
      )}
      
      {/* Display error if available */}
      {task.error && (
        <div className="mb-6">
          <h3 className="text-md font-medium mb-2">Error</h3>
          <StatusMessage type="error" message={task.error} />
        </div>
      )}
      
      {/* Loading indicator for in-progress tasks */}
      {isLoading && (
        <div className="flex items-center space-x-2 text-gray-600 mt-4">
          <span>Processing task</span>
          <LoadingDots />
        </div>
      )}
    </div>
  );
} 