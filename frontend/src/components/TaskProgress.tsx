'use client'

import React from 'react';

export type TaskStatus = 'pending' | 'in-progress' | 'done' | 'failed';

export interface Task {
  id: string | number;
  title: string;
  status: TaskStatus;
  subtasks?: Task[];
}

interface TaskProgressProps {
  tasks: Task[];
  className?: string;
  showSubtasks?: boolean;
}

export default function TaskProgress({ tasks, className = '', showSubtasks = true }: TaskProgressProps) {
  // Calculate overall progress 
  const calculateProgress = (tasksList: Task[]): number => {
    const total = tasksList.length;
    if (total === 0) return 0;
    
    const completed = tasksList.filter(task => task.status === 'done').length;
    return (completed / total) * 100;
  };
  
  const progress = calculateProgress(tasks);
  
  // Get the status color
  const getStatusColor = (status: TaskStatus): string => {
    switch (status) {
      case 'pending':
        return 'bg-gray-200 text-gray-700';
      case 'in-progress':
        return 'bg-blue-200 text-blue-700';
      case 'done':
        return 'bg-green-200 text-green-700';
      case 'failed':
        return 'bg-red-200 text-red-700';
      default:
        return 'bg-gray-200 text-gray-700';
    }
  };
  
  // Get the status icon
  const getStatusIcon = (status: TaskStatus): JSX.Element => {
    switch (status) {
      case 'pending':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'in-progress':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        );
      case 'done':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };
  
  const renderTask = (task: Task, level: number = 0): JSX.Element => {
    const statusColor = getStatusColor(task.status);
    const statusIcon = getStatusIcon(task.status);
    
    return (
      <div key={task.id} className={`mb-2 ${level > 0 ? 'ml-6' : ''}`}>
        <div className="flex items-center">
          <div className={`flex items-center justify-center w-5 h-5 rounded-full mr-2 ${statusColor}`}>
            {statusIcon}
          </div>
          <div className="flex-grow">
            <div className="flex items-center justify-between">
              <span className="font-medium">{task.title}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${statusColor}`}>
                {task.status}
              </span>
            </div>
          </div>
        </div>
        
        {showSubtasks && task.subtasks && task.subtasks.length > 0 && (
          <div className="mt-2 border-l-2 border-gray-200 pl-2">
            {task.subtasks.map(subtask => renderTask(subtask, level + 1))}
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className={`task-progress ${className}`}>
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            Progress: {Math.round(progress)}%
          </span>
          <span className="text-sm text-gray-500">
            {tasks.filter(task => task.status === 'done').length}/{tasks.length} tasks completed
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
      
      <div className="mt-4 space-y-1">
        {tasks.map(task => renderTask(task))}
      </div>
    </div>
  );
} 