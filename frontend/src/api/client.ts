import axios, { AxiosInstance, AxiosError } from 'axios';
import { logNetworkTiming } from '@/utils/perfLogger';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api', // Proxied to http://localhost:5000/api by Vite
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const requestConfig = config as typeof config & { metadata?: { startTime: number } };
    requestConfig.metadata = {
      startTime: typeof performance !== 'undefined' ? performance.now() : Date.now(),
    };

    // Add any auth tokens here if needed in the future
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    const responseConfig = response.config as typeof response.config & {
      metadata?: { startTime?: number };
    };

    const startTime = responseConfig.metadata?.startTime;
    if (typeof startTime === 'number' && typeof performance !== 'undefined') {
      const duration = performance.now() - startTime;
      logNetworkTiming({
        phase: 'success',
        method: response.config.method,
        url: response.config.url,
        status: response.status,
        durationMs: duration,
      });
    }

    return response;
  },
  (error: AxiosError) => {
    const errorConfig = error.config as typeof error.config & {
      metadata?: { startTime?: number };
    };
    const startTime = errorConfig?.metadata?.startTime;
    if (typeof startTime === 'number' && typeof performance !== 'undefined') {
      const duration = performance.now() - startTime;
      logNetworkTiming({
        phase: 'error',
        method: errorConfig?.method,
        url: errorConfig?.url,
        status: error.response?.status,
        durationMs: duration,
      });
    }

    // Handle common errors
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: No response from server');
    } else {
      // Error in request setup
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
