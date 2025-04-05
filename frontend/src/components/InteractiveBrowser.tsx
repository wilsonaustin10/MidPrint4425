import { useState, useEffect } from 'react';
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
  error?: string;
  actionIndicators?: ActionIndicator[]; // New prop for showing action indicators
}

interface HighlightedElement {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  label?: string; // New property to show a label for the highlighted element
  type?: 'target' | 'hover' | 'focus'; // New property to indicate the type of highlight
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
  error,
  actionIndicators = []
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [visibleIndicators, setVisibleIndicators] = useState<ActionIndicator[]>([]);
  const [previousUrl, setPreviousUrl] = useState('');
  const [showTransition, setShowTransition] = useState(false);
  
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
  
  // URL change detection for transitions
  useEffect(() => {
    if (currentUrl && currentUrl !== previousUrl) {
      // URL has changed, show transition effect
      setShowTransition(true);
      
      // After transition period, hide it and update previous URL
      const timer = setTimeout(() => {
        setShowTransition(false);
        setPreviousUrl(currentUrl);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [currentUrl, previousUrl]);
  
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

  return (
    <div className="flex flex-col bg-white shadow rounded-lg overflow-hidden">
      {/* URL Bar and Controls */}
      <div className="border-b p-2 flex items-center bg-gray-100">
        <div className="flex items-center space-x-2 mr-2">
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
        
        <div className="flex-grow px-3 py-1 bg-white border rounded flex items-center">
          {currentUrl ? (
            <div className="flex items-center w-full">
              {isLoading && (
                <div className="mr-2">
                  <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              )}
              <TransitionEffect
                isVisible={showTransition}
                type="fade"
                duration={500}
              >
                <span className="truncate text-sm text-blue-600 font-medium">
                  {currentUrl}
                </span>
              </TransitionEffect>
              
              {!showTransition && (
                <span className="truncate text-sm text-gray-600">
                  {currentUrl}
                </span>
              )}
            </div>
          ) : (
            <span className="text-sm text-gray-400">No URL loaded</span>
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
                  return <ScrollIndicator key={indicator.id} x={indicator.x} y={indicator.y} direction={indicator.y > window.innerHeight / 2 ? 'down' : 'up'} />;
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