'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import ChatBox, { Message } from '@/components/ChatBox'
import TaskView from '@/components/TaskView'
import { useTaskContext } from '@/lib/TaskContext'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isSplitView, setIsSplitView] = useState<boolean>(true)
  const searchParams = useSearchParams()
  const { createTask, currentTask } = useTaskContext()
  
  useEffect(() => {
    // Check for initial task from URL parameters
    const taskParam = searchParams.get('task')
    if (taskParam) {
      // Add the task as the first user message
      setMessages([
        {
          role: 'user',
          content: taskParam
        }
      ])
    }
  }, [searchParams])

  const handleMessageSent = async (message: Message) => {
    setMessages(prev => [...prev, message]);
    
    if (message.role === 'user') {
      try {
        // Add a temporary thinking message
        const thinkingMessage: Message = {
          role: 'assistant',
          content: 'Thinking...',
          status: 'loading'
        };
        
        setMessages(prev => [...prev, thinkingMessage]);
        
        // Create a task for the user's message
        await createTask('Browser Task', message.content);
        
        // The actual response will come via WebSockets through the TaskContext
        // which will be displayed in the TaskView component
      } catch (error) {
        console.error('Error creating task:', error);
        
        // Add error message
        setMessages(prev => {
          // Remove the thinking message
          const withoutThinking = prev.slice(0, -1);
          
          // Add the error message
          return [...withoutThinking, {
            role: 'assistant',
            content: 'Sorry, there was an error processing your request. Please try again.',
            status: 'error'
          }];
        });
      }
    }
  };

  // Toggle between split view and chat-only view
  const toggleView = () => {
    setIsSplitView(!isSplitView);
  };

  return (
    <div className="flex flex-col h-screen max-h-screen">
      <header className="bg-white shadow">
        <div className="mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            <Link href="/">MidPrint</Link> - Chat
          </h1>
          <div className="flex space-x-4">
            <button
              onClick={toggleView}
              className="text-gray-600 hover:text-gray-800 focus:outline-none"
              aria-label={isSplitView ? "Hide task view" : "Show task view"}
            >
              {isSplitView ? (
                <span className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                  Chat Only
                </span>
              ) : (
                <span className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm11 1H6v8h8V6z" clipRule="evenodd" />
                  </svg>
                  Split View
                </span>
              )}
            </button>
            <Link href="/browser" className="text-blue-600 hover:text-blue-800">
              View Browser
            </Link>
          </div>
        </div>
      </header>
      
      <main className="flex-grow overflow-hidden bg-gray-50">
        <div className="h-full max-w-7xl mx-auto p-4">
          {isSplitView ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-[calc(100vh-8rem)]">
              {/* Chat panel */}
              <div className="bg-white shadow rounded-lg overflow-hidden">
                <ChatBox 
                  initialMessages={messages} 
                  onMessageSent={handleMessageSent} 
                />
              </div>
              
              {/* Task view panel */}
              <div className="bg-white shadow rounded-lg overflow-auto">
                <TaskView />
              </div>
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg h-[calc(100vh-8rem)]">
              <ChatBox 
                initialMessages={messages} 
                onMessageSent={handleMessageSent} 
              />
            </div>
          )}
        </div>
      </main>
    </div>
  )
} 