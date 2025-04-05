/**
 * SessionManager - Manages user session state, including task history, preferences, and authentication
 */

'use client';

import { v4 as uuidv4 } from 'uuid';

// Define interfaces
export interface SavedTask {
  id: string;
  description: string;
  timestamp: number;
  status: 'completed' | 'failed' | 'canceled';
  result?: any;
  error?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  showAnimations: boolean;
  notificationDuration: number;
  hideOnboarding: boolean;
}

export interface UserSession {
  userId: string;
  isAuthenticated: boolean;
  lastActive: number;
  preferences: UserPreferences;
  recentTasks: SavedTask[];
  recentUrls: string[];
  hasCompletedOnboarding: boolean;
}

// Default values
const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'system',
  showAnimations: true,
  notificationDuration: 5000,
  hideOnboarding: false,
};

const DEFAULT_SESSION: UserSession = {
  userId: '',
  isAuthenticated: false,
  lastActive: 0,
  preferences: DEFAULT_PREFERENCES,
  recentTasks: [],
  recentUrls: [],
  hasCompletedOnboarding: false,
};

// Maximum number of items in history
const MAX_HISTORY_ITEMS = 10;

/**
 * SessionManager class handles user session management
 */
class SessionManager {
  private static instance: SessionManager;
  private session: UserSession;
  private readonly storageKey = 'midprint_user_session';
  private readonly authTokenKey = 'auth_token';

  private constructor() {
    // Initialize session from localStorage or with defaults
    this.session = this.loadSession();
    
    // Set or verify user ID
    if (!this.session.userId) {
      this.session.userId = uuidv4();
      this.saveSession();
    }
    
    // Update last active time
    this.updateLastActive();
  }

  /**
   * Get the SessionManager instance (singleton pattern)
   */
  public static getInstance(): SessionManager {
    if (typeof window === 'undefined') {
      // Return a temporary instance for server-side rendering
      return new SessionManager();
    }
    
    if (!SessionManager.instance) {
      SessionManager.instance = new SessionManager();
    }
    return SessionManager.instance;
  }

  /**
   * Load session from localStorage
   */
  private loadSession(): UserSession {
    if (typeof window === 'undefined') {
      return { ...DEFAULT_SESSION };
    }
    
    try {
      const storedSession = window.localStorage.getItem(this.storageKey);
      if (!storedSession) {
        return { ...DEFAULT_SESSION };
      }
      
      const parsedSession = JSON.parse(storedSession) as UserSession;
      
      // Ensure all fields exist in case the stored format is outdated
      return {
        ...DEFAULT_SESSION,
        ...parsedSession,
        preferences: {
          ...DEFAULT_PREFERENCES,
          ...parsedSession.preferences,
        },
      };
    } catch (error) {
      console.error('Error loading session:', error);
      return { ...DEFAULT_SESSION };
    }
  }

  /**
   * Save session to localStorage
   */
  private saveSession(): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      window.localStorage.setItem(this.storageKey, JSON.stringify(this.session));
    } catch (error) {
      console.error('Error saving session:', error);
    }
  }

  /**
   * Update last active timestamp
   */
  public updateLastActive(): void {
    this.session.lastActive = Date.now();
    this.saveSession();
  }

  /**
   * Check if user is authenticated
   */
  public isAuthenticated(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }
    
    try {
      return !!window.localStorage.getItem(this.authTokenKey);
    } catch (e) {
      console.error('Error accessing localStorage:', e);
      return false;
    }
  }

  /**
   * Get session information
   */
  public getSession(): UserSession {
    // Always ensure session has latest authentication status
    this.session.isAuthenticated = this.isAuthenticated();
    return { ...this.session };
  }

  /**
   * Update user preferences
   */
  public updatePreferences(preferences: Partial<UserPreferences>): UserPreferences {
    this.session.preferences = {
      ...this.session.preferences,
      ...preferences,
    };
    this.saveSession();
    return { ...this.session.preferences };
  }

  /**
   * Add a task to recent tasks history
   */
  public addRecentTask(task: SavedTask): void {
    this.session.recentTasks = [
      task,
      ...this.session.recentTasks
        .filter(t => t.id !== task.id) // Remove duplicates
        .slice(0, MAX_HISTORY_ITEMS - 1), // Keep only the most recent items
    ];
    this.saveSession();
  }

  /**
   * Add a URL to recent URLs history
   */
  public addRecentUrl(url: string): void {
    if (!url || !url.trim()) return;
    
    this.session.recentUrls = [
      url,
      ...this.session.recentUrls
        .filter(u => u !== url) // Remove duplicates
        .slice(0, MAX_HISTORY_ITEMS - 1), // Keep only the most recent items
    ];
    this.saveSession();
  }

  /**
   * Get recent tasks
   */
  public getRecentTasks(): SavedTask[] {
    return [...this.session.recentTasks];
  }

  /**
   * Get recent URLs
   */
  public getRecentUrls(): string[] {
    return [...this.session.recentUrls];
  }

  /**
   * Clear task history
   */
  public clearTaskHistory(): void {
    this.session.recentTasks = [];
    this.saveSession();
  }

  /**
   * Clear URL history
   */
  public clearUrlHistory(): void {
    this.session.recentUrls = [];
    this.saveSession();
  }

  /**
   * Check if user has completed onboarding
   */
  public hasCompletedOnboarding(): boolean {
    return this.session.hasCompletedOnboarding;
  }

  /**
   * Mark onboarding as completed
   */
  public completeOnboarding(): void {
    this.session.hasCompletedOnboarding = true;
    this.saveSession();
  }

  /**
   * Reset onboarding status (for testing/debugging)
   */
  public resetOnboarding(): void {
    this.session.hasCompletedOnboarding = false;
    this.saveSession();
  }

  /**
   * Clear the session data
   */
  public clearSession(): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      window.localStorage.removeItem(this.storageKey);
      window.localStorage.removeItem(this.authTokenKey);
      this.session = { ...DEFAULT_SESSION };
    } catch (error) {
      console.error('Error clearing session:', error);
    }
  }
}

// Export the SessionManager class as the default export
export default SessionManager; 