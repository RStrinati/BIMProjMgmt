import axios, { AxiosInstance, AxiosError } from 'axios';
import { logNetworkTiming } from '@/utils/perfLogger';

const envBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : '';
const runtimeProtocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
const fallbackBaseUrl = runtimeHost ? `${runtimeProtocol}//${runtimeHost}:5000/api` : '/api';
const overrideLocalhostEnv =
  Boolean(envBaseUrl) &&
  Boolean(runtimeHost) &&
  !['localhost', '127.0.0.1'].includes(runtimeHost) &&
  (envBaseUrl?.includes('localhost') || envBaseUrl?.includes('127.0.0.1'));
const apiBaseUrl = overrideLocalhostEnv ? fallbackBaseUrl : envBaseUrl || '/api';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: apiBaseUrl, // Defaults to Vite proxy or explicit env override
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const frontendLogUrl = `${apiBaseUrl.replace(/\/$/, '')}/logs/frontend`;
const shouldLogUrl = (url?: string | null) => !!url && !url.includes('/logs/frontend');

const logFrontendEvent = (event: Record<string, unknown>) => {
  if (typeof window === 'undefined' || !frontendLogUrl || !shouldLogUrl(String(event?.url ?? ''))) {
    return;
  }
  void fetch(frontendLogUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
    keepalive: true,
  }).catch(() => undefined);
};

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const requestConfig = config as typeof config & { metadata?: { startTime: number } };
    requestConfig.metadata = {
      startTime: typeof performance !== 'undefined' ? performance.now() : Date.now(),
    };
    logFrontendEvent({
      level: 'debug',
      message: 'request:start',
      context: {
        method: requestConfig.method,
        url: requestConfig.url,
      },
    });

    return config;
  },
  (error) => Promise.reject(error),
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
      logFrontendEvent({
        level: 'info',
        message: 'request:success',
        context: {
          method: response.config.method,
          url: response.config.url,
          status: response.status,
          duration: duration.toFixed(1),
        },
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
      logFrontendEvent({
        level: 'error',
        message: 'request:error',
        context: {
          method: errorConfig?.method,
          url: errorConfig?.url,
          status: error.response?.status,
          duration: duration.toFixed(1),
          message: error.message,
        },
      });
    }

    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('Network Error: No response from server');
    } else {
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  },
);

export { frontendLogUrl };
export default apiClient;
