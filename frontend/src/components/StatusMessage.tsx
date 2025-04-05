'use client'

import React from 'react';
import LoadingDots from './LoadingDots';

export type StatusType = 'info' | 'success' | 'warning' | 'error' | 'loading';

interface StatusMessageProps {
  type: StatusType;
  message: string;
  className?: string;
}

export default function StatusMessage({ type, message, className = '' }: StatusMessageProps) {
  // Style configurations based on status type
  const configs = {
    info: {
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-700',
      borderColor: 'border-blue-200',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      )
    },
    success: {
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
      borderColor: 'border-green-200',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      )
    },
    warning: {
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-700',
      borderColor: 'border-yellow-200',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      )
    },
    error: {
      bgColor: 'bg-red-50',
      textColor: 'text-red-700',
      borderColor: 'border-red-200',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    },
    loading: {
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-700',
      borderColor: 'border-gray-200',
      icon: null
    }
  };
  
  const { bgColor, textColor, borderColor, icon } = configs[type];
  
  return (
    <div className={`p-4 rounded-md border ${bgColor} ${textColor} ${borderColor} ${className}`}>
      <div className="flex items-start">
        {type === 'loading' ? (
          <div className="flex-shrink-0 mr-3">
            <LoadingDots color="bg-gray-600" size="small" />
          </div>
        ) : (
          <div className="flex-shrink-0 mr-3">
            {icon}
          </div>
        )}
        <div>
          <p>{message}</p>
        </div>
      </div>
    </div>
  );
} 