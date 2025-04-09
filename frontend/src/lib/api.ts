import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Add authorization header if token exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Task management API
export const taskAPI = {
  // Get all tasks
  getTasks: async (status?: string, limit = 100, skip = 0) => {
    try {
      const response = await api.get('/task/tasks', {
        params: { status, limit, skip }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching tasks:', error);
      throw error;
    }
  },
  
  // Get a specific task
  getTask: async (taskId: string) => {
    try {
      const response = await api.get(`/task/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching task ${taskId}:`, error);
      throw error;
    }
  },
  
  // Cancel a task
  cancelTask: async (taskId: string) => {
    try {
      const response = await api.delete(`/task/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error(`Error cancelling task ${taskId}:`, error);
      throw error;
    }
  },
  
  // Clear tasks with optional status filter
  clearTasks: async (status?: string) => {
    try {
      const response = await api.delete('/task/tasks', {
        params: { status }
      });
      return response.data;
    } catch (error) {
      console.error('Error clearing tasks:', error);
      throw error;
    }
  },
  
  // Get task metrics
  getTaskMetrics: async () => {
    try {
      const response = await api.get('/task/tasks/metrics');
      return response.data;
    } catch (error) {
      console.error('Error fetching task metrics:', error);
      throw error;
    }
  }
};

// Agent (browser automation) API
export const agentAPI = {
  // Initialize the agent
  initialize: async () => {
    try {
      const response = await api.post('/agent/initialize');
      return response.data;
    } catch (error) {
      console.error('Error initializing agent:', error);
      throw error;
    }
  },
  
  // Navigate to a URL
  navigateToUrl: async (url: string) => {
    try {
      const response = await api.post('/agent/navigate', { url });
      return response.data;
    } catch (error) {
      console.error('Error navigating to URL:', error);
      throw error;
    }
  },
  
  // Click an element
  clickElement: async (selector: string, index = 0, timeout = 10000) => {
    try {
      const response = await api.post('/agent/click', { 
        selector, 
        index, 
        timeout 
      });
      return response.data;
    } catch (error) {
      console.error('Error clicking element:', error);
      throw error;
    }
  },
  
  // Input text
  inputText: async (selector: string, text: string, delay = 50) => {
    try {
      const response = await api.post('/agent/input', { 
        selector, 
        text, 
        delay 
      });
      return response.data;
    } catch (error) {
      console.error('Error inputting text:', error);
      throw error;
    }
  },
  
  // Get DOM
  getDom: async () => {
    try {
      const response = await api.post('/agent/get-dom', { 
        include_state: true 
      });
      return response.data;
    } catch (error) {
      console.error('Error getting DOM:', error);
      throw error;
    }
  },
  
  // Capture screenshot
  captureScreenshot: async (fullPage = true) => {
    try {
      const response = await api.post('/agent/screenshot', { 
        full_page: fullPage 
      });
      return response.data;
    } catch (error) {
      console.error('Error capturing screenshot:', error);
      throw error;
    }
  },
  
  // Get current screenshot without creating a task
  getCurrentScreenshot: async () => {
    try {
      const response = await api.get('/agent/screenshot');
      return response.data;
    } catch (error) {
      console.error('Error getting current screenshot:', error);
      throw error;
    }
  },
  
  // Execute natural language task
  executeTask: async (task: string) => {
    try {
      const response = await api.post('/agent/execute', { 
        description: task
      });
      return response.data;
    } catch (error) {
      console.error('Error executing task:', error);
      throw error;
    }
  },
  
  // Get agent status
  getStatus: async () => {
    try {
      const response = await api.get('/agent/status');
      return response.data;
    } catch (error) {
      console.error('Error getting agent status:', error);
      throw error;
    }
  },
  
  // Shutdown agent
  shutdown: async () => {
    try {
      const response = await api.post('/agent/shutdown');
      return response.data;
    } catch (error) {
      console.error('Error shutting down agent:', error);
      throw error;
    }
  }
};

// LLM related API calls
export const llmAPI = {
  // Process a user instruction
  processInstruction: async (instruction: string) => {
    try {
      const response = await api.post('/llm/process', { instruction });
      return response.data;
    } catch (error) {
      console.error('Error processing instruction:', error);
      throw error;
    }
  }
};

// Authentication API
export const authAPI = {
  // Login
  login: async (apiKey: string) => {
    try {
      // Store API key for future requests
      localStorage.setItem('auth_token', apiKey);
      // Verify the key works by making a test call
      const response = await taskAPI.getTaskMetrics();
      return { success: true };
    } catch (error) {
      // If the key is invalid, clear it
      localStorage.removeItem('auth_token');
      console.error('Error during login:', error);
      throw error;
    }
  },
  
  // Logout
  logout: () => {
    localStorage.removeItem('auth_token');
    return { success: true };
  },
  
  // Check if user is logged in
  isLoggedIn: () => {
    return !!localStorage.getItem('auth_token');
  }
};

export default api; 