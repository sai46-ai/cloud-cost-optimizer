import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
export const BACKEND_URL = API_URL.replace('/api/v1', '');

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Lightweight in-memory cache for GET requests
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 2 * 60 * 1000; // 2 minutes

const getCached = async (url: string, config?: any) => {
  const key = url + JSON.stringify(config?.params || {});
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return { data: cached.data };
  }
  const response = await api.get(url, config);
  cache.set(key, { data: response.data, timestamp: Date.now() });
  return response;
};

// Request interceptor for auth token and cache invalidation
api.interceptors.request.use(
  (config) => {
    // Invalidate GET cache on mutations
    const method = config.method?.toLowerCase();
    if (method && ['post', 'put', 'delete', 'patch'].includes(method)) {
      cache.clear();
    }

    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for unified error handling
api.interceptors.response.use(
  (response) => {
    // If a request succeeds, we know we are online
    window.dispatchEvent(new Event('api-online'));
    return response;
  },
  (error) => {
    if (!error.response) {
      // Network errors (CORS, offline, ERR_CONNECTION_REFUSED, etc.)
      console.warn('API Network Error or Timeout:', error.message);
      window.dispatchEvent(new Event('api-offline'));
      // Return a predictable error format without rejecting brutally
      return Promise.reject(new Error('Unable to connect to the server. Please check your connection.'));
    }

    const status = error.response.status;
    const data = error.response.data;

    // Handle 401 Unauthorized (Expired token or invalid auth)
    if (status === 401) {
      console.warn('Authentication failed or token expired. Clearing session.');
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.dispatchEvent(new Event('auth-expired'));
      
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/') {
         window.location.href = '/login';
      }
    }

    let message = data?.detail || data?.message || error.message;
    if (typeof message === 'object') {
      message = JSON.stringify(message);
    }
    
    console.error(`API Error ${status}:`, message);
    return Promise.reject(new Error(message));
  }
);

export const costService = {
  getDashboard: () => getCached('/costs/dashboard').then(res => res.data),
  getBreakdown: (start?: string, end?: string) => 
    getCached('/costs/breakdown', { params: { start_date: start, end_date: end } }).then(res => res.data),
  getCosts: (start?: string, end?: string, service?: string) =>
    getCached('/costs/', { params: { start_date: start, end_date: end, service } }).then(res => res.data),
};

export const budgetService = {
  getBudgets: () => getCached('/budgets/').then(res => res.data),
  createBudget: (data: any) => api.post('/budgets/', data).then(res => res.data),
  updateBudget: (id: string, data: any) => api.put(`/budgets/${id}`, data).then(res => res.data),
  deleteBudget: (id: string) => api.delete(`/budgets/${id}`).then(res => res.data),
};

export const recommendationService = {
  getRecommendations: () => getCached('/recommendations/').then(res => res.data),
  getSummary: () => getCached('/recommendations/summary').then(res => res.data),
  getIdleResources: () => getCached('/recommendations/idle-resources').then(res => res.data),
  updateStatus: (id: string, status: string) => api.put(`/recommendations/${id}/status`, { status }).then(res => res.data),
};

export const anomalyService = {
  getAnomalies: () => getCached('/anomalies/').then(res => res.data),
  getSummary: () => getCached('/anomalies/summary').then(res => res.data),
  detect: () => api.post('/anomalies/detect').then(res => res.data),
};

export const aiService = {
  getForecasts: () => getCached('/forecasts/').then(res => res.data),
  generateForecasts: () => api.post('/forecasts/generate').then(res => res.data),
  chat: (message: string) => api.post('/assistant/chat', { message }).then(res => res.data),
};

export const setupService = {
  health: () => getCached('/health').then(res => res.data),
};

export const reportService = {
  getReports: () => getCached('/reports/').then(res => res.data),
  generateReport: (data: { report_type: string; format: string }) => api.post('/reports/generate', data).then(res => res.data),
  deleteReport: (id: string) => api.delete(`/reports/${id}`).then(res => res.data),
};

export const authService = {
  login: (data: any) => api.post('/auth/login', data).then(res => res.data),
  register: (data: any) => api.post('/auth/register', data).then(res => res.data),
  getProfile: () => api.get('/auth/me').then(res => res.data), // Intentionally uncached to get fresh profile data
  updateProfile: (data: any) => api.put('/auth/me', data).then(res => res.data),
  changePassword: (data: any) => api.post('/auth/change-password', data).then(res => res.data),
};

export const settingsService = {
  getSettings: () => getCached('/settings/').then(res => res.data),
  updateSettings: (data: any) => api.put('/settings/', data).then(res => res.data),
  getAWSAccount: () => getCached('/settings/aws').then(res => res.data),
  updateAWSAccount: (data: any) => api.put('/settings/aws', data).then(res => res.data),
};

export const auditService = {
  getAuditLogs: (page = 1, pageSize = 20) => api.get('/audit-logs', { params: { page, page_size: pageSize } }).then(res => res.data),
};
