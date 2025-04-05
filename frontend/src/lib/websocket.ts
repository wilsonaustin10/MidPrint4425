'use client';

import { v4 as uuidv4 } from 'uuid';

// Define message type
interface WebSocketMessage {
  type: string;
  [key: string]: any;
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
  private globalMessageHandlers: ((msg: WebSocketMessage) => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private pingIntervalId: NodeJS.Timeout | null = null;
  private lastPongTime = 0;
  private isBrowser: boolean;
  private isConnecting: boolean = false;
  private connectionTimeout: NodeJS.Timeout | null = null;
  private backendAvailable: boolean = true;

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

    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    this.reconnectAttempts = 0;
  }

  subscribeToTask(taskId: string, callback: (data: any) => void): () => void {
    // Register the callback
    if (!this.taskSubscriptions.has(taskId)) {
      this.taskSubscriptions.set(taskId, []);
    }
    this.taskSubscriptions.get(taskId)?.push(callback);

    // If connected, send subscription message
    if (this.isConnected()) {
      this.send({
        type: 'subscribe_task',
        task_id: taskId
      });
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

  send(data: any): void {
    if (this.isConnected()) {
      this.ws?.send(JSON.stringify(data));
    } else if (this.isBrowser && !this.backendAvailable) {
      // If backend is unavailable, provide fallback behavior for task operations
      if (data.type === 'subscribe_task' && data.task_id) {
        console.log(`WebSocket backend unavailable: Would subscribe to task ${data.task_id}`);
        // In a real application, you could potentially fetch task data via REST API here
      }
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

    // Subscribe to tasks
    const taskIds = Array.from(this.taskSubscriptions.keys());
    for (const taskId of taskIds) {
      this.send({
        type: 'subscribe_task',
        task_id: taskId
      });
    }

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

      // Handle task updates
      if (message.type === 'task_update' && message.task_id) {
        const callbacks = this.taskSubscriptions.get(message.task_id) || [];
        callbacks.forEach(callback => {
          try {
            callback(message.data);
          } catch (e) {
            console.error('Error in task subscription callback:', e);
          }
        });
      }

      // Call global message handlers
      this.globalMessageHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (e) {
          console.error('Error in global message handler:', e);
        }
      });
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.warn(`WebSocket closed with code ${event.code}, reason: ${event.reason}`);
    this.ws = null;
    this.isConnecting = false;
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }

    this.attemptReconnect();
  }

  private handleError(event: Event): void {
    console.warn('WebSocket error:', event);
    this.isConnecting = false;
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn(`Maximum reconnection attempts (${this.maxReconnectAttempts}) reached. Backend may be unavailable.`);
      this.backendAvailable = false;
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
    }
    
    this.reconnectTimeoutId = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private sendPing(): void {
    if (this.isConnected()) {
      this.send({
        type: 'ping',
        timestamp: Date.now()
      });
    }
  }
}

// Create a singleton instance of the WebSocket service wrapped in a function
// to ensure it's only initialized on the client side
let websocketServiceInstance: WebSocketServiceInterface | null = null;

// Create a dummy service for SSR
const dummyService: WebSocketServiceInterface = {
  connect: () => {},
  disconnect: () => {},
  subscribeToTask: () => (() => {}),
  addMessageHandler: () => (() => {}),
  isConnected: () => false,
  send: () => {}
};

// Export the service - dummy for SSR, real implementation for client
const websocketService: WebSocketServiceInterface = 
  typeof window === 'undefined' ? dummyService : (
    websocketServiceInstance || (websocketServiceInstance = new WebSocketServiceImpl())
  );

// If in browser, attempt connection after a short delay to allow components to render
if (typeof window !== 'undefined') {
  setTimeout(() => {
    websocketService.connect();
  }, 500);
}

export default websocketService; 