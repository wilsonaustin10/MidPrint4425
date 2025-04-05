'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import SessionManager, { UserSession, UserPreferences, SavedTask } from './SessionManager';

// Define context interface
interface SessionContextType {
  session: UserSession;
  isAuthenticated: boolean;
  preferences: UserPreferences;
  recentTasks: SavedTask[];
  recentUrls: string[];
  hasCompletedOnboarding: boolean;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  addRecentTask: (task: SavedTask) => void;
  addRecentUrl: (url: string) => void;
  clearTaskHistory: () => void;
  clearUrlHistory: () => void;
  clearSession: () => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
}

// Create context with default values
const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Provider component
export const SessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const sessionManager = SessionManager.getInstance();
  const [session, setSession] = useState<UserSession>(sessionManager.getSession());

  // Keep track of session changes
  useEffect(() => {
    // Update last active time on component mount
    sessionManager.updateLastActive();
    
    // Set up regular interval to update last active time
    const intervalId = setInterval(() => {
      sessionManager.updateLastActive();
    }, 60000); // Every minute
    
    // Clean up interval
    return () => clearInterval(intervalId);
  }, []);

  // Helper functions that update session state after manager operations
  const updatePreferences = (preferences: Partial<UserPreferences>) => {
    sessionManager.updatePreferences(preferences);
    setSession(sessionManager.getSession());
  };

  const addRecentTask = (task: SavedTask) => {
    sessionManager.addRecentTask(task);
    setSession(sessionManager.getSession());
  };

  const addRecentUrl = (url: string) => {
    sessionManager.addRecentUrl(url);
    setSession(sessionManager.getSession());
  };

  const clearTaskHistory = () => {
    sessionManager.clearTaskHistory();
    setSession(sessionManager.getSession());
  };

  const clearUrlHistory = () => {
    sessionManager.clearUrlHistory();
    setSession(sessionManager.getSession());
  };

  const clearSession = () => {
    sessionManager.clearSession();
    setSession(sessionManager.getSession());
  };

  const completeOnboarding = () => {
    sessionManager.completeOnboarding();
    setSession(sessionManager.getSession());
  };

  const resetOnboarding = () => {
    sessionManager.resetOnboarding();
    setSession(sessionManager.getSession());
  };

  // Extract commonly used values from session
  const { isAuthenticated, preferences, recentTasks, recentUrls } = session;
  const hasCompletedOnboarding = sessionManager.hasCompletedOnboarding();

  // Construct context value
  const contextValue: SessionContextType = {
    session,
    isAuthenticated,
    preferences,
    recentTasks,
    recentUrls,
    hasCompletedOnboarding,
    updatePreferences,
    addRecentTask,
    addRecentUrl,
    clearTaskHistory,
    clearUrlHistory,
    clearSession,
    completeOnboarding,
    resetOnboarding,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

// Custom hook for using session context
export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

export default SessionContext; 