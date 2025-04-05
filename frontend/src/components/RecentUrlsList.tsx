'use client'

import React from 'react';
import { useSession } from '@/lib/SessionContext';

interface RecentUrlsListProps {
  onSelectUrl?: (url: string) => void;
  className?: string;
}

const RecentUrlsList: React.FC<RecentUrlsListProps> = ({ 
  onSelectUrl,
  className = '' 
}) => {
  const { recentUrls, clearUrlHistory } = useSession();

  if (recentUrls.length === 0) {
    return (
      <div className={`text-center p-4 ${className}`}>
        <p className="text-gray-500">No recent URLs</p>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-700">Recent URLs</h3>
        {recentUrls.length > 0 && (
          <button 
            onClick={clearUrlHistory}
            className="text-sm text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            Clear History
          </button>
        )}
      </div>
      
      <ul className="space-y-2">
        {recentUrls.map((url, index) => {
          // Try to extract favicon and domain
          let favicon = '';
          let domain = '';
          
          try {
            const urlObj = new URL(url);
            domain = urlObj.hostname;
            favicon = `${urlObj.protocol}//${urlObj.hostname}/favicon.ico`;
          } catch (e) {
            // If URL is invalid, just use the raw string
            domain = url;
          }
          
          return (
            <li key={index} className="bg-white border rounded-md shadow-sm hover:shadow">
              <button
                onClick={() => onSelectUrl && onSelectUrl(url)}
                className="w-full p-3 text-left flex items-center space-x-3 focus:outline-none"
                disabled={!onSelectUrl}
              >
                {favicon && (
                  <div className="flex-shrink-0 w-5 h-5 relative">
                    <img 
                      src={favicon} 
                      alt=""
                      className="w-5 h-5"
                      onError={(e) => {
                        // If favicon fails to load, show a generic icon
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <svg 
                        className="w-4 h-4 text-gray-400" 
                        style={{ display: 'none' }}
                        onError={(e) => {
                          // Show the generic icon when image fails
                          (e.target as SVGElement).style.display = 'block';
                        }}
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" 
                        />
                      </svg>
                    </div>
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {domain}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {url}
                  </p>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default RecentUrlsList; 