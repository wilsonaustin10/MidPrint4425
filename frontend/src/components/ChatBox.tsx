'use client'

import React, { useState, useRef, useEffect } from 'react';
import LoadingDots from './LoadingDots';
import StatusMessage, { StatusType } from './StatusMessage';
import MarkdownContent from './MarkdownContent';
import TaskProgress, { Task } from './TaskProgress';

export type Message = {
  role: 'user' | 'assistant';
  content: string;
  status?: StatusType;
  isMarkdown?: boolean;
  tasks?: Task[];
};

interface ChatBoxProps {
  initialMessages?: Message[];
  onMessageSent?: (message: Message) => void;
}

export default function ChatBox({ initialMessages = [], onMessageSent }: ChatBoxProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sample tasks for demo
  const sampleTasks: Task[] = [
    {
      id: '1', 
      title: 'Setup project structure',
      status: 'done'
    },
    {
      id: '2',
      title: 'Implement backend agent',
      status: 'done',
      subtasks: [
        { id: '2.1', title: 'Setup browser management', status: 'done' },
        { id: '2.2', title: 'Create controller service', status: 'done' },
        { id: '2.3', title: 'Implement core actions', status: 'done' }
      ]
    },
    {
      id: '3',
      title: 'Create WebSocket connection',
      status: 'done',
    },
    {
      id: '4',
      title: 'Implement task manager service',
      status: 'done',
    },
    {
      id: '5',
      title: 'Create backend API endpoints',
      status: 'done',
    },
    {
      id: '6',
      title: 'Develop frontend chat interface',
      status: 'in-progress',
      subtasks: [
        { id: '6.1', title: 'Implement basic ChatBox', status: 'done' },
        { id: '6.2', title: 'Add loading and error handling', status: 'done' },
        { id: '6.3', title: 'Implement message formatting', status: 'in-progress' }
      ]
    }
  ];

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Update messages when initialMessages change
  useEffect(() => {
    if (initialMessages.length > 0) {
      setMessages(initialMessages);
    }
  }, [initialMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Reset error state
    setError(null);
    
    // Add user message to chat
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    
    // Call the onMessageSent callback if provided
    if (onMessageSent) {
      setIsLoading(true);
      try {
        await onMessageSent(userMessage);
      } catch (error) {
        console.error('Error in onMessageSent callback:', error);
        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError('An unexpected error occurred');
        }
      } finally {
        setIsLoading(false);
      }
    }
    
    // Clear the input field
    setInput('');
  };

  const retryLastMessage = () => {
    if (messages.length < 1) return;
    
    // Find the last user message
    const lastUserMessageIndex = [...messages].reverse().findIndex(m => m.role === 'user');
    
    if (lastUserMessageIndex === -1) return;
    
    // Get the actual index in the original array
    const userMessageIndex = messages.length - 1 - lastUserMessageIndex;
    const userMessage = messages[userMessageIndex];
    
    // Remove all messages after the user message
    setMessages(messages.slice(0, userMessageIndex + 1));
    
    // Set input to the last message content for easy editing
    setInput(userMessage.content);
  };

  const renderMessageContent = (message: Message) => {
    if (message.isMarkdown) {
      return <MarkdownContent content={message.content} />;
    } else if (message.tasks) {
      return (
        <div className="mt-2">
          <TaskProgress tasks={message.tasks} />
        </div>
      );
    } else {
      return <p>{message.content}</p>;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {error && (
        <div className="px-4 py-2">
          <StatusMessage 
            type="error" 
            message={error}
            className="mb-4"
          />
        </div>
      )}
      
      <div className="flex-grow overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No messages yet. Start a conversation below!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-blue-100 ml-12' 
                    : message.status === 'error'
                      ? 'bg-red-50 mr-12'
                      : 'bg-gray-100 mr-12'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <p className="font-semibold">
                    {message.role === 'user' ? 'You' : 'MidPrint Agent'}
                  </p>
                  {message.status && message.role === 'assistant' && (
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      message.status === 'error' ? 'bg-red-200 text-red-800' :
                      message.status === 'success' ? 'bg-green-200 text-green-800' :
                      message.status === 'warning' ? 'bg-yellow-200 text-yellow-800' :
                      'bg-blue-200 text-blue-800'
                    }`}>
                      {message.status}
                    </span>
                  )}
                </div>
                
                {renderMessageContent(message)}
                
                {message.status === 'error' && message.role === 'assistant' && (
                  <div className="mt-2">
                    <button 
                      onClick={retryLastMessage}
                      className="text-sm text-red-700 hover:text-red-800 hover:underline flex items-center"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Retry
                    </button>
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="bg-gray-100 p-4 rounded-lg mr-12">
                <p className="font-semibold mb-2">MidPrint Agent</p>
                <div className="flex items-center space-x-2">
                  <span>Thinking</span>
                  <LoadingDots />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="mt-4 p-4 border-t">
        <div className="flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your instructions here..."
            className="flex-grow p-4 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-4 rounded-r-lg hover:bg-blue-700 disabled:bg-blue-300 flex items-center"
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? (
              <>
                <span className="mr-2">Sending</span>
                <LoadingDots size="small" color="bg-white" />
              </>
            ) : (
              'Send'
            )}
          </button>
        </div>
      </form>
    </div>
  );
} 