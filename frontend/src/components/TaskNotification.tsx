'use client'

import React, { useEffect, useState } from 'react';

interface TaskNotificationProps {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  title?: string;
  duration?: number;
  onClose?: () => void;
}

const TaskNotification: React.FC<TaskNotificationProps> = ({
  type,
  message,
  title,
  duration = 5000,
  onClose
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [animation, setAnimation] = useState('translate-y-0 opacity-100');
  
  // Set up auto-dismiss
  useEffect(() => {
    const dismissTimeout = setTimeout(() => {
      setAnimation('translate-y-2 opacity-0');
      
      // Wait for animation to complete before removing
      const removeTimeout = setTimeout(() => {
        setIsVisible(false);
        if (onClose) onClose();
      }, 300);
      
      return () => clearTimeout(removeTimeout);
    }, duration);
    
    return () => clearTimeout(dismissTimeout);
  }, [duration, onClose]);

  // Handle manual close
  const handleClose = () => {
    setAnimation('translate-y-2 opacity-0');
    setTimeout(() => {
      setIsVisible(false);
      if (onClose) onClose();
    }, 300);
  };

  if (!isVisible) return null;

  // Configure styles based on notification type
  const styles = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: (
        <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: title || 'Success',
      titleColor: 'text-green-800'
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: (
        <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: title || 'Error',
      titleColor: 'text-red-800'
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: (
        <svg className="w-6 h-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      title: title || 'Warning',
      titleColor: 'text-yellow-800'
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: (
        <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: title || 'Information',
      titleColor: 'text-blue-800'
    }
  };

  const currentStyle = styles[type];

  return (
    <div 
      className={`fixed top-4 right-4 max-w-sm w-full shadow-lg rounded-lg pointer-events-auto transition-all duration-300 transform ${animation}`}
      role="alert"
    >
      <div className={`${currentStyle.bg} border ${currentStyle.border} rounded-lg shadow-md overflow-hidden`}>
        <div className="p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              {currentStyle.icon}
            </div>
            <div className="ml-3 w-0 flex-1 pt-0.5">
              <p className={`text-sm font-medium ${currentStyle.titleColor}`}>{currentStyle.title}</p>
              <p className="mt-1 text-sm text-gray-700">{message}</p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                className="bg-transparent rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                onClick={handleClose}
              >
                <span className="sr-only">Close</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskNotification; 