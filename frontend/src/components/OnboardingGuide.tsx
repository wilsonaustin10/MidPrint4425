'use client'

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import SessionManager from '@/lib/SessionManager';
import TransitionEffect from './TransitionEffect';

interface OnboardingStep {
  title: string;
  description: string;
  image?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface OnboardingGuideProps {
  onComplete?: () => void;
  defaultOpen?: boolean;
}

export const OnboardingGuide: React.FC<OnboardingGuideProps> = ({ 
  onComplete,
  defaultOpen = true 
}) => {
  const router = useRouter();
  const sessionManager = SessionManager.getInstance();
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasSeenOnboarding, setHasSeenOnboarding] = useState(true);

  // Define the onboarding steps
  const steps: OnboardingStep[] = [
    {
      title: 'Welcome to MidPrint',
      description: 'MidPrint is an AI-powered browser automation agent that helps you complete web tasks using natural language instructions.',
      image: '/images/onboarding/welcome.svg',
    },
    {
      title: 'Chat Interface',
      description: 'Use the chat interface to give instructions to the agent. Try asking it to navigate to websites, click on elements, fill out forms, and more.',
      image: '/images/onboarding/chat.svg',
      action: {
        label: 'Go to Chat',
        onClick: () => router.push('/chat')
      }
    },
    {
      title: 'Browser View',
      description: 'Watch the agent perform tasks in real-time in the embedded browser view. You can see exactly what the agent is doing and how it interacts with websites.',
      image: '/images/onboarding/browser.svg',
      action: {
        label: 'Go to Browser',
        onClick: () => router.push('/browser')
      }
    },
    {
      title: 'Session Management',
      description: 'MidPrint automatically saves your recent tasks and browsing history. You can pick up where you left off at any time. All your data is stored locally on your device and not shared with any third parties.',
      image: '/images/onboarding/browser.svg',
    },
    {
      title: 'Sample Tasks',
      description: 'Here are some examples of what you can ask the agent to do:\n• "Go to google.com and search for cats"\n• "Fill out a contact form"\n• "Find the top news headlines"',
      image: '/images/onboarding/examples.svg',
    },
    {
      title: 'Ready to Start',
      description: 'You\'re all set! Start automating your web tasks with MidPrint.',
      image: '/images/onboarding/ready.svg',
      action: {
        label: 'Get Started',
        onClick: () => handleComplete()
      }
    }
  ];

  // Check if the user has completed onboarding
  useEffect(() => {
    const hasCompletedOnboarding = sessionManager.hasCompletedOnboarding();
    setHasSeenOnboarding(hasCompletedOnboarding);
    setIsOpen(defaultOpen && !hasCompletedOnboarding);
  }, [defaultOpen]);

  // Handle next step
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  // Handle previous step
  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Handle skip/complete
  const handleComplete = () => {
    sessionManager.completeOnboarding();
    setIsOpen(false);
    if (onComplete) {
      onComplete();
    }
  };

  // Handle reopen onboarding
  const handleOpenOnboarding = () => {
    setCurrentStep(0);
    setIsOpen(true);
  };

  if (hasSeenOnboarding && !isOpen) {
    return (
      <button 
        onClick={handleOpenOnboarding}
        className="absolute bottom-4 right-4 bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label="Open guide"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    );
  }

  return (
    <TransitionEffect isVisible={isOpen} type="fade" duration={300}>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          {/* Progress indicator */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gray-200">
            <div 
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
          
          {/* Close button */}
          <button
            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 focus:outline-none"
            onClick={handleComplete}
            aria-label="Close onboarding"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          {/* Content */}
          <div className="p-6 pt-8">
            <TransitionEffect 
              key={currentStep}
              isVisible={true} 
              type="slide-up" 
              duration={300}
            >
              <div className="flex flex-col items-center text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {steps[currentStep].title}
                </h2>
                
                {steps[currentStep].image && (
                  <div className="w-full max-h-64 flex justify-center mb-6">
                    <img 
                      src={steps[currentStep].image} 
                      alt={steps[currentStep].title} 
                      className="max-h-full object-contain"
                    />
                  </div>
                )}
                
                <p className="text-gray-600 whitespace-pre-line mb-8">
                  {steps[currentStep].description}
                </p>
              </div>
            </TransitionEffect>
          </div>
          
          {/* Actions */}
          <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-between">
            <div>
              {currentStep > 0 ? (
                <button
                  onClick={handlePrevious}
                  className="px-4 py-2 text-blue-600 hover:text-blue-800 focus:outline-none"
                >
                  Previous
                </button>
              ) : (
                <button
                  onClick={handleComplete}
                  className="px-4 py-2 text-gray-500 hover:text-gray-700 focus:outline-none"
                >
                  Skip
                </button>
              )}
            </div>
            
            <div className="flex space-x-4">
              <div className="text-xs text-gray-500 self-center">
                {currentStep + 1} of {steps.length}
              </div>
              
              {steps[currentStep].action ? (
                <button
                  onClick={steps[currentStep].action.onClick}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  {steps[currentStep].action.label}
                </button>
              ) : (
                <button
                  onClick={handleNext}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  {currentStep < steps.length - 1 ? 'Next' : 'Get Started'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </TransitionEffect>
  );
};

export default OnboardingGuide; 