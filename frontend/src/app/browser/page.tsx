'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import InteractiveBrowser from '@/components/InteractiveBrowser'
import { useTaskContext } from '@/lib/TaskContext'
import { agentAPI } from '@/lib/api'
import { v4 as uuidv4 } from 'uuid'
import { useNotification } from '@/components/NotificationContainer'
import TransitionEffect from '@/components/TransitionEffect'
import websocketService, { WebSocketMessage } from '@/lib/websocket'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/use-toast'
import { ArrowLeft, ArrowRight, RefreshCw, Eye, Info, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useBrowserHistory } from '@/hooks/useBrowserHistory'
import { useCurrentTask } from '@/hooks/useCurrentTask'

// Type for highlighted elements
interface HighlightedElement {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  type: 'target' | 'focus' | 'hover' | 'info';
  label?: string;
  expiry?: number; // Timestamp when this highlight should expire
  color?: string; // Optional color override
}

interface ActionIndicator {
  id: string;
  type: 'click' | 'typing' | 'navigation' | 'scroll' | 'hover';
  x: number;
  y: number;
  timestamp: number;
  duration: number; // Duration in milliseconds
  content?: string;
  direction?: 'up' | 'down';
}

// Cache for storing recently received screenshots
const CACHE_SIZE = 10;
class ScreenshotCache {
  private cache: Map<string, string> = new Map();
  private keys: string[] = [];
  
  set(key: string, value: string): void {
    // If key already exists, remove it so we can reorder
    if (this.cache.has(key)) {
      this.keys = this.keys.filter(k => k !== key);
    }
    
    // Add to cache and keys
    this.cache.set(key, value);
    this.keys.push(key);
    
    // Keep cache size limited
    if (this.keys.length > CACHE_SIZE) {
      const oldestKey = this.keys.shift();
      if (oldestKey) this.cache.delete(oldestKey);
    }
  }
  
  get(key: string): string | undefined {
    return this.cache.get(key);
  }
  
  has(key: string): boolean {
    return this.cache.has(key);
  }
  
  clear(): void {
    this.cache.clear();
    this.keys = [];
  }
}

// Performance metrics tracking
const PERF_METRICS = {
  screenshotsReceived: 0,
  screenshotsRendered: 0,
  lastReceiveTime: 0,
  totalRenderTime: 0,
  avgRenderTime: 0,
  renderTimes: [] as number[],
  droppedFrames: 0
};

export default function BrowserPage() {
  const [url, setUrl] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [screenshot, setScreenshot] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [highlightedElements, setHighlightedElements] = useState<HighlightedElement[]>([]);
  const [actionIndicators, setActionIndicators] = useState<ActionIndicator[]>([]);
  const [transitionState, setTransitionState] = useState<'idle' | 'starting' | 'completed' | 'failed'>('idle');
  const [isConnected, setIsConnected] = useState(false);
  
  const { currentTask } = useTaskContext();
  const { showNotification } = useNotification();
  const screenshotTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const wsSubscriptionRef = useRef<(() => void) | null>(null);

  // Refs
  const screenshotRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<number>(0);
  const screenshotCache = useRef<ScreenshotCache>(new ScreenshotCache());
  const lastRenderedImage = useRef<string>('');
  const pendingScreenshot = useRef<string | null>(null);
  const renderPending = useRef<boolean>(false);

  // Config state
  const [screenshotConfig, setScreenshotConfig] = useState({
    quality: 75,
    format: 'jpeg',
    debounce: 100
  });
  
  // Debounced update screenshot
  const debouncedSetScreenshot = useCallback((newScreenshot: string) => {
    // Store in cache with timestamp as key
    const key = `screenshot_${Date.now()}`;
    screenshotCache.current.set(key, newScreenshot);
    
    // If we're not currently rendering, update immediately
    if (!renderPending.current) {
      lastRenderedImage.current = newScreenshot;
      setScreenshot(newScreenshot);
      renderPending.current = false;
    } else {
      // Otherwise, store for next render cycle
      pendingScreenshot.current = newScreenshot;
    }
  }, []);

  // Update screenshot with throttling
  const updateScreenshot = useCallback((newScreenshot: string) => {
    // If the new screenshot is the same as the last one, don't update
    if (newScreenshot === lastRenderedImage.current) return;
    
    // If we're already rendering, queue the update
    if (renderPending.current) {
      pendingScreenshot.current = newScreenshot;
      return;
    }
    
    // Mark rendering in progress
    renderPending.current = true;
    
    // Update the screenshot and render
    lastRenderedImage.current = newScreenshot;
    setScreenshot(newScreenshot);
    
    // Set a timeout to check for pending updates
    requestAnimationFrame(() => {
      renderPending.current = false;
      
      // If we have a pending update, process it
      if (pendingScreenshot.current) {
        const next = pendingScreenshot.current;
        pendingScreenshot.current = null;
        updateScreenshot(next);
      }
    });
  }, []);

  // Handle WebSocket connection status
  useEffect(() => {
    const connectionCheckInterval = setInterval(() => {
      setIsConnected(websocketService.isConnected());
    }, 2000);
    
    // Ensure connection is established
    websocketService.connect();
    
    return () => {
      clearInterval(connectionCheckInterval);
    };
  }, []);

  // Monitor current task changes
  useEffect(() => {
    if (currentTask) {
      // If we have task info, show notification that task is active
      if (currentTask.status === 'in_progress') {
        showNotification(
          'info',
          `Processing task: ${currentTask.prompt}`,
          'Task Running'
        );
        setIsLoading(true);
      } else if (currentTask.status === 'completed') {
        showNotification(
          'success',
          `Task completed: ${currentTask.prompt}`,
          'Task Completed'
        );
        setIsLoading(false);
        setTransitionState('completed');
        setTimeout(() => setTransitionState('idle'), 2000);
      } else if (currentTask.status === 'failed') {
        showNotification(
          'error',
          currentTask.error || 'Task failed',
          'Task Failed'
        );
        setIsLoading(false);
        setError(currentTask.error || 'An error occurred during browser operation');
        setTransitionState('failed');
        setTimeout(() => setTransitionState('idle'), 2000);
      }
      
      // Update screenshot and page state from current task
      if (currentTask.screenshot_data) {
        setScreenshot(currentTask.screenshot_data);
      }
      
      if (currentTask.page_state) {
        setUrl(currentTask.page_state.url || '');
        setPageTitle(currentTask.page_state.title || '');
      }
    }
  }, [currentTask, showNotification]);

  // Function to configure screenshot settings on the backend
  const configureScreenshot = async (config: {
    quality?: number;
    format?: 'jpeg' | 'png';
    debounce_interval?: number;
    full_page?: boolean;
  }) => {
    try {
      const response = await fetch('/api/v1/browser/screenshot/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to configure screenshot: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Update local config state
      setScreenshotConfig({
        quality: data.config.quality || screenshotConfig.quality,
        format: data.config.format || screenshotConfig.format,
        debounce: data.debounce_interval || screenshotConfig.debounce
      });
      
      console.log('Screenshot configuration updated:', data.config);
      showNotification('success', 'Screenshot settings updated', 'Configuration');
      
      return data;
    } catch (error) {
      console.error('Error configuring screenshot:', error);
      showNotification('error', `Failed to update screenshot settings: ${error}`, 'Configuration Error');
      return null;
    }
  };

  // Configure screenshot quality based on network conditions and device performance
  useEffect(() => {
    // Function to detect network conditions
    const detectNetworkConditions = () => {
      // Use Network Information API if available
      const connection = (navigator as any).connection;
      if (connection) {
        const effectiveType = connection.effectiveType; // 4g, 3g, 2g, slow-2g
        const downlink = connection.downlink; // Mbps
        
        console.log('Network conditions:', {
          effectiveType,
          downlink,
          rtt: connection.rtt,
          saveData: connection.saveData
        });
        
        // Adjust quality based on network conditions
        if (effectiveType === '4g' && downlink > 5) {
          // Good network, high quality
          return { quality: 85, format: 'jpeg' as const };
        } else if (effectiveType === '4g' || effectiveType === '3g' && downlink > 1) {
          // Medium network, medium quality
          return { quality: 70, format: 'jpeg' as const };
        } else {
          // Slow network, lower quality
          return { quality: 50, format: 'jpeg' as const };
        }
      }
      
      // Fallback if Network Information API is not available
      return { quality: 75, format: 'jpeg' as const };
    };
    
    // Configure screenshot settings based on detected conditions
    const autoConfigureScreenshot = async () => {
      const config = detectNetworkConditions();
      await configureScreenshot({
        ...config,
        debounce_interval: 200, // Conservative default
        full_page: true
      });
    };
    
    // Auto-configure on component mount
    autoConfigureScreenshot();
    
    // Set up a listener for network changes if the API is available
    const connection = (navigator as any).connection;
    if (connection) {
      connection.addEventListener('change', autoConfigureScreenshot);
      return () => {
        connection.removeEventListener('change', autoConfigureScreenshot);
      };
    }
  }, []);

  // Log performance metrics periodically
  useEffect(() => {
    const logInterval = setInterval(() => {
      if (PERF_METRICS.screenshotsReceived > 0) {
        console.debug('Browser Performance Metrics:', {
          screenshotsReceived: PERF_METRICS.screenshotsReceived,
          screenshotsRendered: PERF_METRICS.screenshotsRendered, 
          droppedFrames: PERF_METRICS.droppedFrames,
          avgRenderTime: PERF_METRICS.avgRenderTime.toFixed(2) + 'ms',
          memoryUsage: performance?.memory ? 
            (performance.memory.usedJSHeapSize / (1024 * 1024)).toFixed(2) + 'MB' : 
            'Not available'
        });
      }
    }, 10000); // Log every 10 seconds
    
    return () => clearInterval(logInterval);
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log('WebSocket message:', message);
    
    // Check message type
    if (message.type === 'browser_screenshot_update') {
      // Update screenshot
      PERF_METRICS.screenshotsReceived++;
      PERF_METRICS.lastReceiveTime = Date.now();
      debouncedSetScreenshot(message.screenshot);
    } 
    else if (message.type === 'browser_state_update') {
      // Update URL and title
      setUrl(message.currentUrl || '');
      setPageTitle(message.pageTitle || '');
    }
    else if (message.type === 'browser_action_feedback') {
      // Add appropriate action indicator
      const id = `action_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
      
      if (message.actionType === 'click' && message.data?.x !== undefined && message.data?.y !== undefined) {
        const newIndicator: ActionIndicator = {
          id,
          type: 'click',
          x: message.data.x,
          y: message.data.y,
          timestamp: Date.now(),
          duration: 2000
        };
        setActionIndicators(prev => [...prev, newIndicator]);
      }
      else if (message.actionType === 'typing' && message.data?.x !== undefined && message.data?.y !== undefined) {
        const newIndicator: ActionIndicator = {
          id,
          type: 'typing',
          x: message.data.x,
          y: message.data.y,
          timestamp: Date.now(),
          content: message.data.content || 'Typing...',
          duration: 3000
        };
        setActionIndicators(prev => [...prev, newIndicator]);
      }
      else if (message.actionType === 'navigate') {
        const newIndicator: ActionIndicator = {
          id,
          type: 'navigation',
          x: 0,
          y: 0,
          timestamp: Date.now(),
          duration: 2000
        };
        setActionIndicators(prev => [...prev, newIndicator]);
      }
      else if (message.actionType === 'scroll' && message.data?.x !== undefined && message.data?.y !== undefined) {
        const newIndicator: ActionIndicator = {
          id,
          type: 'scroll',
          x: message.data.x,
          y: message.data.y,
          timestamp: Date.now(),
          direction: message.data.direction as 'up' | 'down',
          duration: 1500
        };
        setActionIndicators(prev => [...prev, newIndicator]);
      }
      else if (message.actionType === 'hover' && message.data?.x !== undefined && message.data?.y !== undefined) {
        const newIndicator: ActionIndicator = {
          id,
          type: 'hover',
          x: message.data.x,
          y: message.data.y,
          timestamp: Date.now(),
          duration: 1500
        };
        setActionIndicators(prev => [...prev, newIndicator]);
      }
    }
    // Handle other message types as needed
  }, [debouncedSetScreenshot]);

  // Subscribe to WebSocket updates when current task changes
  useEffect(() => {
    // Clear previous subscription
    if (wsSubscriptionRef.current) {
      wsSubscriptionRef.current();
      wsSubscriptionRef.current = null;
    }
    
    // If we have a current task, subscribe to its updates
    if (currentTask && currentTask.id) {
      const unsubscribe = websocketService.subscribeToTask(
        currentTask.id,
        handleWebSocketMessage
      );
      wsSubscriptionRef.current = unsubscribe;
      
      console.log(`Subscribed to WebSocket updates for task ${currentTask.id}`);
    }
    
    return () => {
      if (wsSubscriptionRef.current) {
        wsSubscriptionRef.current();
        wsSubscriptionRef.current = null;
      }
    };
  }, [currentTask, handleWebSocketMessage]);

  const addClickIndicator = (x: number, y: number) => {
    const newIndicator: ActionIndicator = {
      id: uuidv4(),
      type: 'click',
      x,
      y,
      timestamp: Date.now(),
      duration: 2500
    };
    setActionIndicators(prev => [...prev, newIndicator]);
  };

  const addTypingIndicator = (x: number, y: number, content: string) => {
    const newIndicator: ActionIndicator = {
      id: uuidv4(),
      type: 'typing',
      x,
      y,
      content,
      timestamp: Date.now(),
      duration: 4000
    };
    setActionIndicators(prev => [...prev, newIndicator]);
  };

  const addNavigationIndicator = () => {
    const newIndicator: ActionIndicator = {
      id: uuidv4(),
      type: 'navigation',
      x: 0,
      y: 0,
      timestamp: Date.now(),
      duration: 3000
    };
    setActionIndicators(prev => [...prev, newIndicator]);
  };

  const addScrollIndicator = (x: number, y: number, direction: 'up' | 'down') => {
    const newIndicator: ActionIndicator = {
      id: uuidv4(),
      type: 'scroll',
      x,
      y,
      direction,
      timestamp: Date.now(),
      duration: 2000
    };
    setActionIndicators(prev => [...prev, newIndicator]);
  };

  const addHoverIndicator = (x: number, y: number) => {
    const newIndicator: ActionIndicator = {
      id: uuidv4(),
      type: 'hover',
      x,
      y,
      timestamp: Date.now(),
      duration: 1500
    };
    setActionIndicators(prev => [...prev, newIndicator]);
  };

  const highlightElement = (element: HighlightedElement) => {
    // Add default expiry of 5 seconds if not provided
    const completeElement = {
      ...element,
      expiry: element.expiry || Date.now() + 5000,
    };
    
    setHighlightedElements(prev => {
      // Remove any existing highlight with the same ID
      const filtered = prev.filter(h => h.id !== element.id);
      return [...filtered, completeElement];
    });
  };

  // Initial screenshot fetch and task status setup
  useEffect(() => {
    const fetchInitialScreenshot = async () => {
      try {
        setIsLoading(true);
        const result = await agentAPI.getCurrentScreenshot();
        if (result.screenshot) {
          setScreenshot(result.screenshot);
        }
        
        if (result.pageInfo) {
          setUrl(result.pageInfo.currentUrl || '');
          setPageTitle(result.pageInfo.title || '');
        }
      } catch (error) {
        console.error('Error fetching initial screenshot:', error);
        setError('Could not fetch browser screenshot. The browser may not be initialized.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialScreenshot();
    
    return () => {
      // Clean up any pending timeouts when component unmounts
      if (screenshotTimeoutRef.current) {
        clearTimeout(screenshotTimeoutRef.current);
      }
    };
  }, []);

  const handleNavigate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url || !url.trim()) {
      showNotification('error', 'Please enter a valid URL', 'URL Error');
      return;
    }
    
    // Reset previous state
    setError('');
    setHighlightedElements([]);
    setActionIndicators([]);
    setIsLoading(true);
    
    try {
      // Show navigation indicator
      addNavigationIndicator();
      
      // Format URL if needed
      let formattedUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        formattedUrl = 'https://' + url;
        setUrl(formattedUrl);
      }
      
      // Navigate to the URL
      const result = await agentAPI.navigateToUrl(formattedUrl);
      
      if (result.status === 'success') {
        setTransitionState('starting');
        
        if (result.screenshot) {
          setScreenshot(result.screenshot);
        }
        
        if (result.pageInfo) {
          setPageTitle(result.pageInfo.title || '');
        }
        
        showNotification('success', `Navigated to ${formattedUrl}`, 'Navigation');
      } else {
        setError(`Navigation failed: ${result.message || 'Unknown error'}`);
        showNotification('error', `Navigation failed: ${result.message || 'Unknown error'}`, 'Navigation Error');
      }
    } catch (error) {
      console.error('Error navigating to URL:', error);
      setError('Failed to navigate to the specified URL. Please try again.');
      showNotification('error', 'Failed to navigate to the specified URL', 'Navigation Error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setError('');
    setIsLoading(true);
      
    try {
      // Show navigation indicator
      addNavigationIndicator();
      
      // Execute a refresh action (navigate to current URL)
      if (url) {
        const result = await agentAPI.navigateToUrl(url);
        
        if (result.status === 'success') {
          if (result.screenshot) {
            setScreenshot(result.screenshot);
          }
          
          if (result.pageInfo) {
            setPageTitle(result.pageInfo.title || '');
          }
          
          showNotification('success', 'Page refreshed', 'Refresh');
        } else {
          setError(`Refresh failed: ${result.message || 'Unknown error'}`);
          showNotification('error', `Refresh failed: ${result.message || 'Unknown error'}`, 'Refresh Error');
        }
      } else {
        setError('No URL to refresh. Please navigate to a page first.');
        showNotification('error', 'No URL to refresh', 'Refresh Error');
      }
    } catch (error) {
      console.error('Error refreshing page:', error);
      setError('Failed to refresh the page. Please try again.');
      showNotification('error', 'Failed to refresh the page', 'Refresh Error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    // Display appropriate notification
    showNotification('info', 'Stopping current operation', 'Operation Stopped');
    
    // Reset loading state and clear errors
    setIsLoading(false);
    setError('');
    
    // Clear indicators
    setActionIndicators([]);
    
    // Take a fresh screenshot to show current state
    const fetchLatestScreenshot = async () => {
      try {
        const result = await agentAPI.getCurrentScreenshot();
        if (result.screenshot) {
          setScreenshot(result.screenshot);
        }
      } catch (error) {
        console.error('Error fetching screenshot after stop:', error);
      }
    };
    
    fetchLatestScreenshot();
  };

  // Handle click inside the screenshot
  const handleScreenshotClick = (event: React.MouseEvent<HTMLImageElement>) => {
    if (!screenshotRef.current) return;
    
    // Get position relative to the image
    const rect = screenshotRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Calculate the normalized position (0-1)
    const normalizedX = x / rect.width;
    const normalizedY = y / rect.top;
    
    // Only highlight for test/debug purposes in development
    const highlight: HighlightedElement = {
      id: `manual-${Date.now()}`,
      x,
      y,
      width: 50,
      height: 50,
      type: 'info',
      label: `${Math.round(x)},${Math.round(y)}`,
      expiry: Date.now() + 3000
    };
    
    // Add the highlight
    setHighlightedElements(prev => [...prev, highlight]);
    
    console.log(`Clicked at ${x},${y} (normalized: ${normalizedX.toFixed(3)},${normalizedY.toFixed(3)})`);
  };

  const goToUrl = async (url: string) => {
    try {
      setIsLoading(true);
      setError('');
      
      // Format URL if needed
      let formattedUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        formattedUrl = `https://${url}`;
      }
      
      // Send navigation request via WebSocket if connected and task is active
      if (websocketService.isConnected() && currentTask) {
        // Send a message to request navigation
        websocketService.send(JSON.stringify({
          type: 'action_request',
          task_id: currentTask.id,
          action: 'go_to_url',
          parameters: { url: formattedUrl }
        }));
        
        // Add navigation indicator
        addNavigationIndicator();
        
        // Set the URL immediately for responsive UI
        setUrl(formattedUrl);
      } else {
        // Fallback to API call if WebSocket is not available
        const response = await fetch('/api/browser/go-to-url', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: formattedUrl }),
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Failed to navigate to URL');
        }
        
        const data = await response.json();
        
        if (data.screenshot) {
          setScreenshot(data.screenshot);
        }
        
        if (data.currentUrl) {
          setUrl(data.currentUrl);
        }
        
        if (data.pageTitle) {
          setPageTitle(data.pageTitle);
        }
      }
    } catch (err) {
      setError(`Navigation error: ${err instanceof Error ? err.message : String(err)}`);
      console.error('Error navigating to URL:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Effect to clean up old highlights and indicators
  useEffect(() => {
    // Set up interval to clean up expired elements
    const interval = setInterval(() => {
      const now = Date.now();
      
      // Clean up action indicators
      setActionIndicators(prev => 
        prev.filter(indicator => now - indicator.timestamp < indicator.duration)
      );
      
      // Clean up highlighted elements
      setHighlightedElements(prev => 
        prev.filter(element => !element.expiry || now < element.expiry)
      );
    }, 500);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen max-h-screen">
      <header className="bg-white shadow">
        <div className="mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            <Link href="/">MidPrint</Link> - Browser View
          </h1>
          <div className="flex items-center space-x-4">
            {!isConnected && (
              <span className="text-red-600 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Disconnected
              </span>
            )}
          <Link href="/chat" className="text-blue-600 hover:text-blue-800">
            Back to Chat
          </Link>
          </div>
        </div>
      </header>
      
      <main className="flex-grow overflow-auto p-4 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <form onSubmit={handleNavigate} className="mb-4">
            <div className="flex">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter a URL"
                className="flex-grow px-4 py-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-r-md transition-colors"
                disabled={isLoading}
              >
                Go
              </button>
            </div>
          </form>
          
          {error && (
            <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          
          <div className="mb-4 flex space-x-2">
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-gray-800 flex items-center"
              disabled={isLoading || !url}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
              </svg>
              Refresh
            </button>
            
            {isLoading && (
              <button
                onClick={handleStop}
                className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-800 flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                </svg>
                Stop
              </button>
            )}
            </div>
          
          <div className="overflow-hidden border rounded-lg shadow-lg"
               onClick={handleScreenshotClick}
          >
            <TransitionEffect
              isVisible={transitionState === 'starting' || transitionState === 'completed' || transitionState === 'failed'}
              type={transitionState === 'failed' ? 'fade' : 'fade'}
              duration={transitionState === 'starting' ? 1000 : 500}
            >
            <InteractiveBrowser
                screenshot={`data:image/png;base64,${screenshot}`}
              currentUrl={url}
              pageTitle={pageTitle}
              isLoading={isLoading}
              highlightedElements={highlightedElements}
                actionIndicators={actionIndicators}
              onRefresh={handleRefresh}
              onStop={handleStop}
                onNavigate={goToUrl}
              error={error}
            />
            </TransitionEffect>
          </div>
        </div>
      </main>
      
      {isLoading && (
        <div className="fixed top-4 right-4 z-50">
          <TransitionEffect
            isVisible={isLoading}
            type={transitionState === 'failed' ? 'fade' : 'fade'}
            duration={300}
          >
            <div className="bg-blue-600 text-white px-4 py-2 rounded-full shadow-lg flex items-center space-x-2">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{pageTitle ? `Loading: ${pageTitle}` : 'Navigating...'}</span>
            </div>
          </TransitionEffect>
        </div>
      )}
    </div>
  )
} 