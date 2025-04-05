'use client'

import React from 'react';
import { useSession } from '@/lib/SessionContext';
import { SavedTask } from '@/lib/SessionManager';
import { formatDistanceToNow } from 'date-fns';

interface RecentTasksListProps {
  onSelectTask?: (taskDescription: string) => void;
  className?: string;
}

const RecentTasksList: React.FC<RecentTasksListProps> = ({ 
  onSelectTask,
  className = '' 
}) => {
  const { recentTasks, clearTaskHistory } = useSession();

  if (recentTasks.length === 0) {
    return (
      <div className={`text-center p-4 ${className}`}>
        <p className="text-gray-500">No recent tasks</p>
      </div>
    );
  }

  // Group tasks by day
  const tasksByDay: Record<string, SavedTask[]> = {};
  
  recentTasks.forEach(task => {
    const date = new Date(task.timestamp);
    const day = date.toLocaleDateString(undefined, { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
    
    if (!tasksByDay[day]) {
      tasksByDay[day] = [];
    }
    
    tasksByDay[day].push(task);
  });

  // Get status icon based on task status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="text-green-500" title="Completed">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </span>
        );
      case 'failed':
        return (
          <span className="text-red-500" title="Failed">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </span>
        );
      case 'canceled':
        return (
          <span className="text-gray-500" title="Canceled">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
            </svg>
          </span>
        );
      default:
        return (
          <span className="text-blue-500" title="Unknown">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          </span>
        );
    }
  };

  return (
    <div className={`${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-700">Recent Tasks</h3>
        {recentTasks.length > 0 && (
          <button 
            onClick={clearTaskHistory}
            className="text-sm text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            Clear History
          </button>
        )}
      </div>
      
      <div className="space-y-6">
        {Object.entries(tasksByDay).map(([day, tasks]) => (
          <div key={day} className="space-y-2">
            <h4 className="text-sm font-medium text-gray-500">{day}</h4>
            <ul className="space-y-2">
              {tasks.map((task) => (
                <li key={task.id} className="bg-white border rounded-md shadow-sm hover:shadow">
                  <button
                    onClick={() => onSelectTask && onSelectTask(task.description)}
                    className="w-full p-3 text-left flex items-start space-x-3 focus:outline-none"
                    disabled={!onSelectTask}
                  >
                    <div className="flex-shrink-0 pt-0.5">
                      {getStatusIcon(task.status)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {task.description}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDistanceToNow(new Date(task.timestamp), { addSuffix: true })}
                      </p>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentTasksList; 