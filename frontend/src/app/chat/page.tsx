'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import ChatBox, { Message } from '../../components/ChatBox'
import { useTasks } from '@/lib/TaskContext'
import { agentAPI } from '@/lib/api'
import { v4 as uuidv4 } from 'uuid'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const { tasks, createTask, cancelTask } = useTasks();
  
  // Handle message sent
  const handleMessageSent = async (message: Message) => {
    // Add message to the chat
    setMessages(prev => [...prev, message]);
    
    // Create a "thinking" message from the assistant
    const thinkingMessage: Message = {
      role: 'assistant',
      content: 'Thinking...',
      status: 'loading'
    };
    
    setMessages(prev => [...prev, thinkingMessage]);
    
    try {
      // Generate a task ID and create it
      const task = await createTask(`Process query: ${message.content}`, message.content);
      
      // Replace the thinking message with the actual response
      setMessages(prev => {
        const newMessages = [...prev];
        const thinkingIndex = newMessages.findIndex(
          m => m.role === 'assistant' && m.status === 'loading'
        );
        
        if (thinkingIndex !== -1) {
          newMessages.splice(thinkingIndex, 1);
        }
        
        return newMessages;
      });
      
      // Add a completed response message
      const responseMessage: Message = {
        role: 'assistant',
        content: 'Your request is being processed.',
        status: 'success',
        isMarkdown: true
      };
      
      setMessages(prev => [...prev, responseMessage]);
    } catch (error) {
      console.error('Error processing message:', error);
      
      // Replace the thinking message with an error message
      setMessages(prev => {
        const newMessages = [...prev];
        const thinkingIndex = newMessages.findIndex(
          m => m.role === 'assistant' && m.status === 'loading'
        );
        
        if (thinkingIndex !== -1) {
          newMessages[thinkingIndex] = {
            role: 'assistant',
            content: 'Sorry, there was an error processing your request. Please try again.',
            status: 'error'
          };
        }
        
        return newMessages;
      });
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-screen">
      <header className="bg-white shadow">
        <div className="mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            <Link href="/">MidPrint</Link> - Chat
          </h1>
          <Link href="/browser" className="text-blue-600 hover:text-blue-800">
            View Browser
          </Link>
        </div>
      </header>
      
      <main className="flex-grow overflow-auto p-4 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6 h-[calc(100vh-16rem)]">
            <ChatBox 
              initialMessages={messages} 
              onMessageSent={handleMessageSent} 
            />
          </div>
        </div>
      </main>
    </div>
  )
} 