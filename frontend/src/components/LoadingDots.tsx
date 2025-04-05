'use client'

import React, { useEffect, useState } from 'react';

interface LoadingDotsProps {
  className?: string;
  color?: string;
  size?: 'small' | 'medium' | 'large';
  speed?: 'slow' | 'normal' | 'fast';
}

export default function LoadingDots({ 
  className = '',
  color = 'bg-gray-600',
  size = 'medium',
  speed = 'normal'
}: LoadingDotsProps) {
  const [dots, setDots] = useState('');
  
  // Determine dot size
  const dotSize = {
    small: 'w-1 h-1',
    medium: 'w-2 h-2',
    large: 'w-3 h-3',
  }[size];
  
  // Determine animation speed
  const animationSpeed = {
    slow: 700,
    normal: 500,
    fast: 300,
  }[speed];

  useEffect(() => {
    const intervalId = setInterval(() => {
      setDots(prevDots => {
        if (prevDots.length >= 3) return '';
        return prevDots + '.';
      });
    }, animationSpeed);
    
    return () => clearInterval(intervalId);
  }, [animationSpeed]);

  return (
    <div className={`flex space-x-2 items-center ${className}`}>
      <div className={`rounded-full ${dotSize} ${color} ${dots.length >= 1 ? 'opacity-100' : 'opacity-30'} transition-opacity duration-200`}></div>
      <div className={`rounded-full ${dotSize} ${color} ${dots.length >= 2 ? 'opacity-100' : 'opacity-30'} transition-opacity duration-200`}></div>
      <div className={`rounded-full ${dotSize} ${color} ${dots.length >= 3 ? 'opacity-100' : 'opacity-30'} transition-opacity duration-200`}></div>
    </div>
  );
} 