'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import InteractiveBrowser from '@/components/InteractiveBrowser'
import { useTasks } from '@/lib/TaskContext'
import { agentAPI } from '@/lib/api'
import { v4 as uuidv4 } from 'uuid'
import { useNotification } from '@/components/NotificationContainer'
import TransitionEffect from '@/components/TransitionEffect'

interface HighlightedElement {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  label?: string;
  type?: 'target' | 'hover' | 'focus';
}

interface ActionIndicator {
  id: string;
  type: 'click' | 'typing' | 'navigation' | 'scroll' | 'hover';
  x: number;
  y: number;
  content?: string;
  timestamp: number;
  duration?: number;
}

export default function BrowserPage() {
  const [url, setUrl] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [screenshot, setScreenshot] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [highlightedElements, setHighlightedElements] = useState<HighlightedElement[]>([]);
  const [actionIndicators, setActionIndicators] = useState<ActionIndicator[]>([]);
  const [transitionState, setTransitionState] = useState<'idle' | 'starting' | 'completed' | 'failed'>('idle');
  
  const { tasks, createTask, cancelTask, getTask } = useTasks();
  const { showNotification } = useNotification();

  const fetchTask = useCallback((taskId: string) => {
    console.log(`Monitoring task: ${taskId}`);
  }, []);

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
      duration: 5000
    };
    setActionIndicators(prev => [...prev, newIndicator]);
  };

  const addScrollIndicator = (x: number, y: number, direction: 'up' | 'down') => {
    const newIndicator: ActionIndicator = {
      id: uuidv4(),
      type: 'scroll',
      x,
      y,
      content: direction,
      timestamp: Date.now(),
      duration: 1500
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
    const elementWithId = {
      ...element,
      id: element.id || uuidv4()
    };
    
    setHighlightedElements(prev => [...prev, elementWithId]);
    
    if (element.type !== 'target') {
      setTimeout(() => {
        setHighlightedElements(prev => 
          prev.filter(el => el.id !== elementWithId.id)
        );
      }, 3000);
    }
  };

  useEffect(() => {
    if (tasks.activeTask) {
      if (tasks.activeTask.status === 'completed' && tasks.activeTask.result) {
        showNotification(
          'success', 
          `Task completed: ${tasks.activeTask.description}`,
          'Task Completed'
        );
        
        setTransitionState('completed');
        setTimeout(() => setTransitionState('idle'), 2000);
        
        setIsLoading(false);
        
        if (tasks.activeTask.result.screenshot) {
          setScreenshot(tasks.activeTask.result.screenshot);
        }
        
        if (tasks.activeTask.result.pageInfo) {
          setPageTitle(tasks.activeTask.result.pageInfo.title || '');
        }

        if (tasks.activeTask.result.elementCoordinates) {
          const { x, y } = tasks.activeTask.result.elementCoordinates;
          
          if (tasks.activeTask.result.elementSize) {
            const { width, height } = tasks.activeTask.result.elementSize;
            
            highlightElement({
              id: `target-${tasks.activeTask.id}`,
              x,
              y,
              width,
              height,
              type: 'target',
              label: tasks.activeTask.result.elementLabel || 'Target Element'
            });
          }
          
          if (tasks.activeTask.description.toLowerCase().includes('click')) {
            addClickIndicator(x, y);
          } else if (tasks.activeTask.description.toLowerCase().includes('type') || 
                     tasks.activeTask.description.toLowerCase().includes('input') || 
                     tasks.activeTask.description.toLowerCase().includes('enter')) {
            const inputText = tasks.activeTask.result.inputText || '';
            addTypingIndicator(x, y, inputText);
          } else if (tasks.activeTask.description.toLowerCase().includes('hover')) {
            addHoverIndicator(x, y);
          } else if (tasks.activeTask.description.toLowerCase().includes('scroll')) {
            const direction = tasks.activeTask.description.toLowerCase().includes('down') ? 'down' : 'up';
            addScrollIndicator(window.innerWidth / 2, y, direction);
          }
        }
        
      } else if (tasks.activeTask.status === 'failed') {
        showNotification(
          'error', 
          tasks.activeTask.error || 'An error occurred during browser operation',
          'Task Failed'
        );
        
        setTransitionState('failed');
        setTimeout(() => setTransitionState('idle'), 2000);
        
        setIsLoading(false);
        setError(tasks.activeTask.error || 'An error occurred during browser operation');
      } else if (tasks.activeTask.status === 'in_progress') {
        showNotification(
          'info', 
          `Starting task: ${tasks.activeTask.description}`,
          'Task Started'
        );
        
        setTransitionState('starting');
        
        setIsLoading(true);
        setError('');

        if (tasks.activeTask.description.toLowerCase().includes('navigate') || 
            tasks.activeTask.description.toLowerCase().includes('refresh')) {
          addNavigationIndicator();
        } else if (tasks.activeTask.description.toLowerCase().includes('scroll')) {
          const direction = tasks.activeTask.description.toLowerCase().includes('up') ? 'up' : 'down';
          addScrollIndicator(window.innerWidth / 2, direction === 'down' ? window.innerHeight * 0.75 : window.innerHeight * 0.25, direction);
        }
      }
    }
  }, [tasks.activeTask, showNotification]);
  
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    const fetchScreenshot = async () => {
      if (!isLoading && !error) {
        try {
          const response = await agentAPI.getCurrentScreenshot();
          if (response.screenshot) {
            setScreenshot(response.screenshot);
          }
          if (response.pageInfo) {
            setPageTitle(response.pageInfo.title || '');
            if (url !== response.pageInfo.url) {
              setUrl(response.pageInfo.url || '');
            }
          }
        } catch (err) {
          console.error('Error fetching current screenshot:', err);
        }
      }
    };
    
    fetchScreenshot();
    
    intervalId = setInterval(fetchScreenshot, 5000);
    
    return () => {
      clearInterval(intervalId);
    };
  }, [isLoading, error, url]);

  const handleNavigate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) return;
    
    setTransitionState('starting');
    setIsLoading(true);
    setError('');
    
    try {
      const taskId = uuidv4();
      
      createTask(taskId, `Navigate to ${url}`);
      
      addNavigationIndicator();
      
      showNotification('info', `Navigating to ${url}`, 'Navigation Started');
      
      const response = await agentAPI.navigateToUrl(url);
      
      if (response.task_id) {
        fetchTask(response.task_id);
      }
    } catch (err: any) {
      setTransitionState('failed');
      setIsLoading(false);
      setError(err.message || 'Failed to navigate to the URL. Please try again.');
      
      showNotification('error', err.message || 'Failed to navigate to the URL', 'Navigation Error');
      
      console.error('Navigation error:', err);
      
      setTimeout(() => setTransitionState('idle'), 2000);
    }
  };

  const handleRefresh = async () => {
    if (url) {
      const taskId = uuidv4();
      createTask(taskId, `Refresh ${url}`);
      
      setTransitionState('starting');
      addNavigationIndicator();
      
      showNotification('info', `Refreshing page: ${url}`, 'Refresh Started');
      
      try {
        const response = await agentAPI.navigateToUrl(url);
        if (response.task_id) {
          fetchTask(response.task_id);
        }
      } catch (err: any) {
        setTransitionState('failed');
        setError(err.message || 'Failed to refresh the page');
        
        showNotification('error', err.message || 'Failed to refresh the page', 'Refresh Error');
        
        console.error('Refresh error:', err);
        
        setTimeout(() => setTransitionState('idle'), 2000);
      }
    }
  };

  const handleStop = () => {
    if (tasks.activeTask && tasks.activeTask.status === 'in_progress') {
      try {
        agentAPI.shutdown();
        
        setIsLoading(false);
        setTransitionState('idle');
        
        showNotification('warning', 'Browser operation was stopped', 'Operation Stopped');
      } catch (err) {
        console.error('Error stopping browser:', err);
      }
    }
  };

  const handleScreenshotClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    addClickIndicator(x, y);
  };

  return (
    <div className="flex flex-col h-screen max-h-screen">
      <header className="bg-white shadow">
        <div className="mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            <Link href="/">MidPrint</Link> - Browser View
          </h1>
          <Link href="/chat" className="text-blue-600 hover:text-blue-800">
            Back to Chat
          </Link>
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
          
          <TransitionEffect
            isVisible={transitionState === 'starting'}
            type="fade"
            className="mb-4"
          >
            <div className="bg-blue-50 border border-blue-200 rounded p-3 text-blue-700 flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Starting browser operation...
            </div>
          </TransitionEffect>
          
          <TransitionEffect
            isVisible={transitionState === 'completed'}
            type="slide-up"
            className="mb-4"
          >
            <div className="bg-green-50 border border-green-200 rounded p-3 text-green-700 flex items-center">
              <svg className="h-5 w-5 mr-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Task completed successfully!
            </div>
          </TransitionEffect>
          
          <TransitionEffect
            isVisible={transitionState === 'failed'}
            type="slide-up"
            className="mb-4"
          >
            <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 flex items-center">
              <svg className="h-5 w-5 mr-3 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              {error || 'Task failed with an error'}
            </div>
          </TransitionEffect>
          
          <div className="h-full" onClick={handleScreenshotClick}>
            <InteractiveBrowser
              screenshot={screenshot}
              currentUrl={url}
              pageTitle={pageTitle}
              isLoading={isLoading}
              highlightedElements={highlightedElements}
              onRefresh={handleRefresh}
              onStop={handleStop}
              error={error}
              actionIndicators={actionIndicators}
            />
          </div>
        </div>
      </main>
    </div>
  );
} 