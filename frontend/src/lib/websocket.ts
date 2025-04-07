'use client';

import { v4 as uuidv4 } from 'uuid';

// Define message type
export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// Message queue item interface
interface QueueItem {
  message: any;
  retry?: boolean;
  maxRetries?: number;
  retries?: number;
}

// Interface for WebSocket service
interface WebSocketServiceInterface {
  connect: () => void;
  disconnect: () => void;
  subscribeToTask: (taskId: string, callback: (data: any) => void) => () => void;
  addMessageHandler: (handler: (msg: WebSocketMessage) => void) => () => void;
  isConnected: () => boolean;
  send: (data: any) => void;
}

/**
 * SSR-safe WebSocket service
 * 
 * This creates a safe wrapper around the WebSocket API that:
 * 1. Works during server-side rendering
 * 2. Only accesses browser APIs on the client
 * 3. Still connects to the backend service
 */
class WebSocketServiceImpl implements WebSocketServiceInterface {
  private ws: WebSocket | null = null;
  private clientId: string = '';
  private url: string = '';
  private taskSubscriptions = new Map<string, ((data: any) => void)[]>();
  private messageQueue: QueueItem[] = [];
  private globalMessageHandlers: ((msg: WebSocketMessage) => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10; // Increased from 5 to 10
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private pingIntervalId: NodeJS.Timeout | null = null;
  private messageProcessingIntervalId: NodeJS.Timeout | null = null;
  private lastPongTime = 0;
  private isBrowser: boolean;
  private isConnecting: boolean = false;
  private connectionTimeout: NodeJS.Timeout | null = null;
  private backendAvailable: boolean = true;
  private pendingSubscriptions: string[] = [];

  constructor() {
    // Check if we're in a browser environment
    this.isBrowser = typeof window !== 'undefined';
    
    // Default client ID (will be replaced if we can access localStorage)
    this.clientId = uuidv4();
    
    // Only execute browser-only code in the browser environment
    if (this.isBrowser) {
      try {
        const storedId = window.localStorage.getItem('ws_client_id');
        if (storedId) {
          this.clientId = storedId;
        } else {
          window.localStorage.setItem('ws_client_id', this.clientId);
        }
      } catch (e) {
        console.error('Error accessing localStorage:', e);
      }
    }
    
    // Set backend WebSocket URL
    this.url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws';
  }

  connect(): void {
    // Don't attempt to connect during SSR
    if (!this.isBrowser) return;
    
    // Don't reconnect if already connected, connecting, or max attempts reached
    // or if backend has been determined to be unavailable
    if (this.isConnecting || 
        (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) ||
        this.reconnectAttempts >= this.maxReconnectAttempts ||
        !this.backendAvailable) {
      return;
    }

    // Set connecting flag to prevent multiple connection attempts
    this.isConnecting = true;

    // Connect to the WebSocket backend
    const wsUrl = `${this.url}?client_id=${this.clientId}`;
    
    try {
      this.ws = new WebSocket(wsUrl);

      // Set up event handlers
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      
      // Set connection timeout
      this.connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.warn('WebSocket connection timed out, closing and retrying...');
          this.ws.close();
          this.isConnecting = false;
          this.attemptReconnect();
        }
      }, 10000); // 10 second timeout
    } catch (error) {
      console.warn('Error creating WebSocket:', error);
      this.isConnecting = false;
      this.attemptReconnect();
    }
  }

  disconnect(): void {
    if (!this.isBrowser) return;
    
    this.isConnecting = false;
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }

    if (this.messageProcessingIntervalId) {
      clearInterval(this.messageProcessingIntervalId);
      this.messageProcessingIntervalId = null;
    }

    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    this.reconnectAttempts = 0;
  }

  subscribeToTask(taskId: string, callback: (data: any) => void): () => void {
    if (!taskId) {
      console.warn('Attempted to subscribe with invalid taskId');
      return () => {};
    }

    // Register the callback
    if (!this.taskSubscriptions.has(taskId)) {
      this.taskSubscriptions.set(taskId, []);
    }
    
    const callbacks = this.taskSubscriptions.get(taskId) || [];
    
    // Only add the callback if it's not already registered
    if (!callbacks.includes(callback)) {
      callbacks.push(callback);
      this.taskSubscriptions.set(taskId, callbacks);
    }

    // If connected, send subscription message
    if (this.isConnected()) {
      this.send({
        type: 'subscribe_task',
        task_id: taskId
      });
    } else {
      // Queue the subscription for when we connect
      if (!this.pendingSubscriptions.includes(taskId)) {
        this.pendingSubscriptions.push(taskId);
        
        // Try to connect if we're not already connecting
        if (!this.isConnecting && !this.ws) {
          this.connect();
        }
      }
    }

    // Return unsubscribe function
    return () => {
      this.unsubscribeFromTask(taskId, callback);
    };
  }

  unsubscribeFromTask(taskId: string, callback: (data: any) => void): void {
    const callbacks = this.taskSubscriptions.get(taskId) || [];
    const index = callbacks.indexOf(callback);
    
    if (index !== -1) {
      callbacks.splice(index, 1);
      
      if (callbacks.length === 0) {
        this.taskSubscriptions.delete(taskId);
        
        // Remove from pending subscriptions if present
        const pendingIndex = this.pendingSubscriptions.indexOf(taskId);
        if (pendingIndex !== -1) {
          this.pendingSubscriptions.splice(pendingIndex, 1);
        }
        
        if (this.isConnected()) {
          this.send({
            type: 'unsubscribe_task',
            task_id: taskId
          });
        }
      } else {
        this.taskSubscriptions.set(taskId, callbacks);
      }
    }
  }

  addMessageHandler(handler: (msg: WebSocketMessage) => void): () => void {
    this.globalMessageHandlers.push(handler);
    return () => {
      const index = this.globalMessageHandlers.indexOf(handler);
      if (index !== -1) {
        this.globalMessageHandlers.splice(index, 1);
      }
    };
  }

  isConnected(): boolean {
    return !!this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  send(data: any, retry = true, maxRetries = 3): void {
    if (this.isConnected()) {
      try {
        this.ws?.send(JSON.stringify(data));
      } catch (e) {
        console.error('Error sending WebSocket message:', e);
        if (retry) {
          this.queueMessage(data, true, maxRetries);
        }
      }
    } else if (retry) {
      // Queue the message to be sent when connection is established
      this.queueMessage(data, true, maxRetries);
      
      // Try to connect if we're not already
      if (!this.isConnecting && !this.ws) {
        this.connect();
      }
    } else if (this.isBrowser && !this.backendAvailable) {
      // If backend is unavailable, provide fallback behavior for task operations
      if (data.type === 'subscribe_task' && data.task_id) {
        console.log(`WebSocket backend unavailable: Would subscribe to task ${data.task_id}`);
      }
    }
  }

  private queueMessage(message: any, retry = true, maxRetries = 3): void {
    // Add message to queue
    this.messageQueue.push({
      message,
      retry,
      maxRetries,
      retries: 0
    });
    
    // Start processing messages if not already processing
    if (!this.messageProcessingIntervalId && this.isBrowser) {
      this.startMessageProcessing();
    }
  }

  private startMessageProcessing(): void {
    if (this.messageProcessingIntervalId) return;
    
    this.messageProcessingIntervalId = setInterval(() => {
      this.processMessageQueue();
    }, 1000);
  }

  private processMessageQueue(): void {
    // Don't process if not connected
    if (!this.isConnected()) return;
    
    // Process up to 5 messages per interval
    const messagesToProcess = Math.min(5, this.messageQueue.length);
    for (let i = 0; i < messagesToProcess; i++) {
      const item = this.messageQueue.shift();
      if (!item) break;
      
      try {
        this.ws?.send(JSON.stringify(item.message));
      } catch (e) {
        console.error('Error sending queued message:', e);
        
        // Re-queue if retry is enabled and max retries not reached
        if (item.retry && (item.retries || 0) < (item.maxRetries || 3)) {
          this.messageQueue.push({
            ...item,
            retries: (item.retries || 0) + 1
          });
        }
      }
    }
    
    // If queue is empty and we're still processing, stop
    if (this.messageQueue.length === 0 && this.messageProcessingIntervalId) {
      clearInterval(this.messageProcessingIntervalId);
      this.messageProcessingIntervalId = null;
    }
  }

  private handleOpen(): void {
    console.log('WebSocket connection established');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.backendAvailable = true;
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }

    // Process pending task subscriptions
    if (this.pendingSubscriptions.length > 0) {
      console.log(`Processing ${this.pendingSubscriptions.length} pending task subscriptions`);
      
      // Create a copy to avoid issues if the array changes during iteration
      const pendingTasks = [...this.pendingSubscriptions];
      
      // Clear pending subscriptions
      this.pendingSubscriptions = [];
      
      // Subscribe to each task
      for (const taskId of pendingTasks) {
        if (this.taskSubscriptions.has(taskId)) {
          this.send({
            type: 'subscribe_task',
            task_id: taskId
          });
        }
      }
    }

    // Start the message queue processor
    this.startMessageProcessing();

    // Set up ping interval
    this.pingIntervalId = setInterval(() => {
      this.sendPing();
    }, 30000);
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;

      // Handle heartbeat/pong messages
      if (message.type === 'heartbeat' || message.type === 'pong') {
        this.lastPongTime = Date.now();
      }

      // Handle connection established message - could include information about available features
      if (message.type === 'connection_established') {
        console.log('Connection established with server', message);
      }

      // Handle task updates
      if (message.type === 'task_update' && message.task_id) {
        const callbacks = this.taskSubscriptions.get(message.task_id) || [];
        callbacks.forEach(callback => {
          try {
            callback(message.data);
          } catch (error) {
            console.error(`Error in task subscription callback for task ${message.task_id}:`, error);
          }
        });
      }

      // Pass message to all global handlers
      this.globalMessageHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in global message handler:', error);
        }
      });
    } catch (error) {
      console.error('Error parsing WebSocket message:', error, event.data);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket connection closed: ${event.code} - ${event.reason}`);
    
    this.ws = null;
    this.isConnecting = false;
    
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }

    // Only attempt to reconnect if it wasn't a clean closure
    // and we haven't reached the max attempts
    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.attemptReconnect();
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn(`WebSocket reconnection failed after ${this.maxReconnectAttempts} attempts`);
      this.backendAvailable = false;
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    
    // Clean up the connection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnecting = false;
    this.attemptReconnect();
  }

  private attemptReconnect(): void {
    // Don't attempt to reconnect if we're already reconnecting
    if (this.reconnectTimeoutId) return;
    
    this.reconnectAttempts++;
    
    // Exponential backoff with jitter
    const baseDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000);
    const jitter = Math.random() * 1000;
    const delay = baseDelay + jitter;
    
    console.log(`WebSocket reconnecting in ${Math.round(delay / 1000)} seconds (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectTimeoutId = null;
      this.connect();
    }, delay);
  }

  private sendPing(): void {
    if (this.isConnected()) {
      this.send({
        type: 'ping',
        timestamp: Date.now(),
      }, false); // Don't retry pings
    }
  }
}

// Create a singleton instance
const websocketService = new WebSocketServiceImpl();

export default websocketService; 