'use client'

import React, { useEffect, useState } from 'react';

interface TransitionEffectProps {
  isVisible: boolean;
  type: 'fade' | 'slide-up' | 'slide-down' | 'zoom' | 'bounce';
  duration?: number;
  delay?: number;
  className?: string;
  children: React.ReactNode;
}

const TransitionEffect: React.FC<TransitionEffectProps> = ({
  isVisible,
  type,
  duration = 300,
  delay = 0,
  className = '',
  children
}) => {
  const [shouldRender, setShouldRender] = useState(isVisible);
  
  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
    } else {
      const timer = setTimeout(() => {
        setShouldRender(false);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration]);
  
  if (!shouldRender) return null;
  
  // Define transition classes based on type
  const getTransitionStyles = (): string => {
    const baseStyles = `transition-all duration-${duration} delay-${delay}`;
    
    switch (type) {
      case 'fade':
        return `${baseStyles} ${isVisible ? 'opacity-100' : 'opacity-0'}`;
      case 'slide-up':
        return `${baseStyles} transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`;
      case 'slide-down':
        return `${baseStyles} transform ${isVisible ? 'translate-y-0 opacity-100' : '-translate-y-8 opacity-0'}`;
      case 'zoom':
        return `${baseStyles} transform ${isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'}`;
      case 'bounce':
        return `${baseStyles} ${isVisible ? 'animate-bounce' : 'opacity-0'}`;
      default:
        return baseStyles;
    }
  };
  
  return (
    <div 
      className={`${getTransitionStyles()} ${className}`}
      style={{ 
        transitionDuration: `${duration}ms`, 
        transitionDelay: `${delay}ms` 
      }}
    >
      {children}
    </div>
  );
};

export default TransitionEffect; 