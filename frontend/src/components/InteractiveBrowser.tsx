import { useState, useEffect, useRef, FormEvent } from 'react';
import Image from 'next/image';
import TransitionEffect from './TransitionEffect';

interface InteractiveBrowserProps {
  screenshot?: string; // base64 encoded screenshot
  currentUrl?: string;
  pageTitle?: string;
  isLoading?: boolean;
  highlightedElements?: HighlightedElement[];
  onRefresh?: () => void;
  onStop?: () => void;
  onNavigate?: (url: string) => void; // New prop for URL navigation
  error?: string;
  actionIndicators?: ActionIndicator[];
}

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

// New interface for action indicators
interface ActionIndicator {
  id: string;
  type: 'click' | 'typing' | 'navigation' | 'scroll' | 'hover'; // Added scroll and hover types
  x: number;
  y: number;
  content?: string; // For typing indicators to show the text being typed
  timestamp: number; // To control when to remove the indicator
  duration?: number; // Optional duration to control how long the indicator is shown
}

// Click indicator component - Enhanced with better animation and visibility
const ClickIndicator: React.FC<{ x: number; y: number }> = ({ x, y }) => (
  <div 
    className="absolute pointer-events-none z-30"
    style={{ 
      left: `${x}px`, 
      top: `${y}px`, 
      transform: 'translate(-50%, -50%)' 
    }}
  >
    {/* Outer ripple effect */}
    <div className="w-12 h-12 rounded-full bg-yellow-400 opacity-50 animate-ping absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
    
    {/* Middle ripple */}
    <div className="w-8 h-8 rounded-full bg-yellow-500 opacity-60 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-ping animation-delay-150" />
    
    {/* Inner circle */}
    <div className="w-4 h-4 rounded-full bg-yellow-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg" />
  </div>
);

// Typing indicator component - Enhanced with better animation and visibility
const TypingIndicator: React.FC<{ x: number; y: number; content?: string }> = ({ x, y, content }) => (
  <div 
    className="absolute pointer-events-none flex items-center z-30"
    style={{ 
      left: `${x}px`, 
      top: `${y}px` 
    }}
  >
    <div className="bg-blue-100 text-blue-800 px-3 py-2 rounded-md text-sm max-w-[250px] truncate shadow-md border border-blue-300 font-medium">
      <span className="flex items-center">
        <svg className="h-4 w-4 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        {content || 'Typing...'}
        <span className="ml-1 inline-block w-2 h-4 bg-blue-500 animate-blink"></span>
      </span>
    </div>
  </div>
);

// Navigation indicator component - Enhanced with better animation and visibility
const NavigationIndicator: React.FC = () => (
  <div className="absolute inset-0 bg-blue-500 bg-opacity-15 pointer-events-none flex items-center justify-center z-30 transition-all duration-300">
    <div className="bg-white px-6 py-3 rounded-lg shadow-xl flex items-center space-x-3 border border-blue-200">
      <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span className="text-blue-700 font-semibold text-lg">Navigating...</span>
    </div>
  </div>
);

// New Scroll indicator component
const ScrollIndicator: React.FC<{ x: number; y: number; direction: 'up' | 'down' }> = ({ x, y, direction }) => (
  <div 
    className="absolute pointer-events-none z-30"
    style={{ 
      left: `${x}px`, 
      top: `${y}px`, 
      transform: 'translate(-50%, -50%)' 
    }}
  >
    <div className="bg-gray-800 bg-opacity-70 text-white px-3 py-2 rounded-full shadow-md flex items-center">
      <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${direction === 'down' ? '' : 'transform rotate-180'}`} viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
      <span className="ml-1 font-medium">{direction === 'down' ? 'Scrolling down' : 'Scrolling up'}</span>
    </div>
  </div>
);

// New Hover indicator component
const HoverIndicator: React.FC<{ x: number; y: number }> = ({ x, y }) => (
  <div 
    className="absolute pointer-events-none z-30"
    style={{ 
      left: `${x}px`, 
      top: `${y}px`, 
      transform: 'translate(-50%, -50%)' 
    }}
  >
    <div className="w-8 h-8 rounded-full border-2 border-indigo-500 bg-indigo-100 bg-opacity-40"></div>
    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-indigo-600 rounded-full"></div>
  </div>
);

const InteractiveBrowser: React.FC<InteractiveBrowserProps> = ({
  screenshot,
  currentUrl = '',
  pageTitle = '',
  isLoading = false,
  highlightedElements = [],
  onRefresh,
  onStop,
  onNavigate,
  error,
  actionIndicators = []
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [visibleIndicators, setVisibleIndicators] = useState<ActionIndicator[]>([]);
  const [previousUrl, setPreviousUrl] = useState('');
  const [showTransition, setShowTransition] = useState(false);
  const [inputUrl, setInputUrl] = useState(currentUrl);
  const [urlHistory, setUrlHistory] = useState<string[]>([]);
  const [isUrlValid, setIsUrlValid] = useState(true);
  const [showUrlHistory, setShowUrlHistory] = useState(false);
  const urlInputRef = useRef<HTMLInputElement>(null);
  
  // Handle image loading to get dimensions for overlay positioning
  useEffect(() => {
    if (screenshot) {
      const img = new window.Image();
      img.onload = () => {
        setImageDimensions({
          width: img.width,
          height: img.height
        });
        setImageLoaded(true);
      };
      img.src = screenshot;
    } else {
      setImageLoaded(false);
    }
  }, [screenshot]);
  
  // URL change detection for transitions and history tracking
  useEffect(() => {
    if (currentUrl) {
      // Update input field with current URL
      setInputUrl(currentUrl);
      
      if (currentUrl !== previousUrl && previousUrl) {
        // URL has changed, show transition effect
        setShowTransition(true);
        
        // Add to URL history if it's a new URL
        if (!urlHistory.includes(currentUrl)) {
          setUrlHistory(prev => [currentUrl, ...prev.slice(0, 9)]);
        }
        
        // After transition period, hide it and update previous URL
        const timer = setTimeout(() => {
          setShowTransition(false);
          setPreviousUrl(currentUrl);
        }, 1000);
        
        return () => clearTimeout(timer);
      } else if (currentUrl && !previousUrl) {
        // Initial URL, just set previousUrl without transition
        setPreviousUrl(currentUrl);
        
        // Add to history if it's not empty
        if (currentUrl.trim() !== '' && !urlHistory.includes(currentUrl)) {
          setUrlHistory(prev => [currentUrl, ...prev.slice(0, 9)]);
        }
      }
    }
  }, [currentUrl, previousUrl, urlHistory]);
  
  // Handle action indicators - add new ones and remove old ones after a timeout
  useEffect(() => {
    if (actionIndicators.length > 0) {
      // Add any new indicators
      setVisibleIndicators(prev => [...prev, ...actionIndicators]);
      
      // Set up cleanup for indicators after they've been displayed for a while
      const now = Date.now();
      const timeoutId = setTimeout(() => {
        setVisibleIndicators(prev => 
          prev.filter(indicator => {
            const duration = indicator.duration || 2000; // Default to 2 seconds if not specified
            return now - indicator.timestamp < duration;
          })
        );
      }, 3000); // Changed from 2000 to 3000 for longer visibility
      
      return () => clearTimeout(timeoutId);
    }
  }, [actionIndicators]);

  // Validate URL format
  const validateUrl = (url: string): boolean => {
    if (!url || url.trim() === '') return false;
    
    // Simple URL validation
    try {
      // Add protocol if missing to avoid URL constructor errors
      const urlToValidate = url.startsWith('http://') || url.startsWith('https://') 
        ? url 
        : `https://${url}`;
      
      new URL(urlToValidate);
      return true;
    } catch (e) {
      return false;
    }
  };

  // Handle URL navigation from address bar
  const handleNavigate = (e: FormEvent) => {
    e.preventDefault();
    
    // Validate URL
    const isValid = validateUrl(inputUrl);
    setIsUrlValid(isValid);
    
    if (!isValid) return;
    
    // Format URL if needed
    let formattedUrl = inputUrl;
    if (!inputUrl.startsWith('http://') && !inputUrl.startsWith('https://')) {
      formattedUrl = `https://${inputUrl}`;
      setInputUrl(formattedUrl);
    }
    
    // Call the navigation callback
    if (onNavigate) {
      onNavigate(formattedUrl);
    }
    
    // Hide URL history dropdown after navigation
    setShowUrlHistory(false);
  };

  // Navigate to a history item
  const navigateToHistoryItem = (url: string) => {
    setInputUrl(url);
    
    if (onNavigate) {
      onNavigate(url);
    }
    
    setShowUrlHistory(false);
  };

  // Focus on URL input when clicking the address bar
  const handleAddressBarClick = () => {
    if (urlInputRef.current) {
      urlInputRef.current.focus();
      urlInputRef.current.select();
    }
  };

  return (
    <div className="flex flex-col bg-white shadow rounded-lg overflow-hidden">
      {/* URL Bar and Controls */}
      <div className="border-b p-2 flex items-center bg-gray-100">
        <div className="flex items-center space-x-2 mr-2">
          {/* Back button - Would need actual browser history integration */}
          <button 
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 transition-colors"
            disabled={true}
            title="Back"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          {/* Forward button - Would need actual browser history integration */}
          <button 
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 transition-colors"
            disabled={true}
            title="Forward"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
          
          {/* Refresh button */}
          {onRefresh && (
            <button 
              onClick={onRefresh}
              disabled={isLoading}
              className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 transition-colors"
              title="Refresh page"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${isLoading ? 'animate-spin text-blue-600' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
          
          {/* Stop button */}
          {onStop && (
            <button 
              onClick={onStop}
              disabled={!isLoading}
              className="p-1 rounded hover:bg-gray-200 disabled:opacity-50 transition-colors"
              title="Stop loading"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        
        {/* Enhanced Address Bar with validation */}
        <div className="flex-grow relative">
          <form onSubmit={handleNavigate}>
            <div 
              className={`px-3 py-1 bg-white border rounded flex items-center ${!isUrlValid ? 'border-red-500' : ''}`}
              onClick={handleAddressBarClick}
            >
              {/* SSL indicator */}
              <div className="mr-2 text-gray-500">
                {currentUrl && (currentUrl.startsWith('https://')) ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-green-600" viewBox="0 0 20 20" fill="currentColor">
                    <title>Secure connection</title>
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <title>Information</title>
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              
              {/* URL Input */}
              <div className="flex-grow relative">
                {isLoading && (
                  <div className="absolute left-0 top-0 bottom-0 flex items-center">
                    <svg className="animate-spin h-4 w-4 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                )}
                
                <input
                  type="text"
                  ref={urlInputRef}
                  value={inputUrl}
                  onChange={(e) => {
                    setInputUrl(e.target.value);
                    setIsUrlValid(true); // Reset validation on change
                  }}
                  onFocus={() => setShowUrlHistory(true)}
                  onBlur={() => setTimeout(() => setShowUrlHistory(false), 200)}
                  className={`w-full text-sm ${isLoading ? 'pl-6' : ''} py-1 focus:outline-none ${!isUrlValid ? 'text-red-600' : 'text-gray-600'}`}
                  placeholder="Enter a URL"
                />
              </div>
              
              {/* Go button */}
              {onNavigate && (
                <button
                  type="submit"
                  className="ml-2 p-1 rounded hover:bg-gray-100 text-blue-600"
                  title="Go to this address"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              )}
            </div>
          </form>
          
          {/* URL validation error message */}
          {!isUrlValid && (
            <div className="absolute left-0 -bottom-5 text-xs text-red-500">
              Please enter a valid URL
            </div>
          )}
          
          {/* URL history dropdown */}
          {showUrlHistory && urlHistory.length > 0 && (
            <div className="absolute z-30 top-full left-0 right-0 mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-y-auto">
              <div className="p-2 border-b text-xs text-gray-500 font-medium">
                Recent URLs
              </div>
              <ul>
                {urlHistory.map((url, index) => (
                  <li key={index}>
                    <button
                      className="w-full text-left px-3 py-2 hover:bg-gray-100 text-sm flex items-center space-x-2"
                      onClick={() => navigateToHistoryItem(url)}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="truncate">{url}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
      
      {/* Page Title with transition effect */}
      {pageTitle && (
        <TransitionEffect
          isVisible={true}
          type="slide-down"
          duration={300}
          className="border-b px-4 py-2 font-medium truncate"
        >
          {pageTitle}
        </TransitionEffect>
      )}
      
      {/* Browser Content Area */}
      <div className="relative flex-grow h-full min-h-[400px] overflow-auto bg-gray-50">
        {error ? (
          <TransitionEffect
            isVisible={!!error}
            type="slide-up"
            duration={300}
          >
            <div className="flex items-center justify-center h-full text-red-500 p-4">
              <div className="text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p>{error}</p>
              </div>
            </div>
          </TransitionEffect>
        ) : isLoading ? (
          <TransitionEffect
            isVisible={isLoading}
            type="fade"
            duration={300}
          >
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading browser content...</p>
              </div>
            </div>
          </TransitionEffect>
        ) : screenshot ? (
          <TransitionEffect
            isVisible={!!screenshot && !isLoading}
            type="fade"
            duration={500}
            className="relative"
          >
            {/* Screenshot Image */}
            <img 
              src={screenshot} 
              alt="Browser screenshot" 
              className="w-full"
              onLoad={() => setImageLoaded(true)}
            />
            
            {/* Highlighted Elements - Enhanced with labels and different styles based on type */}
            {imageLoaded && highlightedElements.map((el) => (
              <div
                key={el.id}
                style={{
                  position: 'absolute',
                  left: `${el.x}px`,
                  top: `${el.y}px`,
                  width: `${el.width}px`,
                  height: `${el.height}px`,
                  border: `2px solid ${el.color || (el.type === 'target' ? '#2563eb' : el.type === 'focus' ? '#10b981' : '#6366f1')}`,
                  backgroundColor: `${el.color || (el.type === 'target' ? '#2563eb' : el.type === 'focus' ? '#10b981' : '#6366f1')}20`,
                  zIndex: 10,
                  pointerEvents: 'none',
                  boxShadow: '0 0 0 4px rgba(37, 99, 235, 0.1)'
                }}
                className="animate-pulse-shadow"
              >
                {el.label && (
                  <div className="absolute top-0 left-0 transform -translate-y-full -translate-x-1/4 bg-white px-2 py-1 text-xs text-blue-700 rounded border border-blue-200 shadow-sm z-20 whitespace-nowrap">
                    {el.label}
                  </div>
                )}
              </div>
            ))}

            {/* Action Indicators - With new types and enhanced display */}
            {imageLoaded && visibleIndicators.map((indicator) => {
              switch (indicator.type) {
                case 'click':
                  return <ClickIndicator key={indicator.id} x={indicator.x} y={indicator.y} />;
                case 'typing':
                  return <TypingIndicator key={indicator.id} x={indicator.x} y={indicator.y} content={indicator.content} />;
                case 'navigation':
                  return <NavigationIndicator key={indicator.id} />;
                case 'scroll':
                  return <ScrollIndicator key={indicator.id} x={indicator.x} y={indicator.y} direction={indicator.content === 'up' ? 'up' : 'down'} />;
                case 'hover':
                  return <HoverIndicator key={indicator.id} x={indicator.x} y={indicator.y} />;
                default:
                  return null;
              }
            })}
          </TransitionEffect>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>No browser content to display</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractiveBrowser; 