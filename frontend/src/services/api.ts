import axios from 'axios';
import useStore from '../store';

// Base URL for the FastAPI backend. Proxy is set up in vite.config.ts to forward /api to http://localhost:8000.
export const BACKEND_URL = '/api/v1';

const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add Authorization token from localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    window.dispatchEvent(new CustomEvent('api-online'));
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor to handle responses and capture connection issues (offline detection)
api.interceptors.response.use(
  (response) => {
    window.dispatchEvent(new CustomEvent('api-online'));
    return response;
  },
  async (error) => {
    if (!error.response) {
      // Network error - backend is offline or unreachable
      window.dispatchEvent(new CustomEvent('api-offline'));
    } else {
      window.dispatchEvent(new CustomEvent('api-online'));
      
      if (error.response.status === 401 || error.response.status === 403) {
        // Clear token and user state to prevent infinite 401 loop
        localStorage.removeItem('access_token');
        try {
          useStore.getState().setAuthenticated(false);
          useStore.getState().setUser(null);
        } catch (e) {
          console.error("Failed to reset auth state:", e);
        }
        
        // Redirect to login if on a protected route
        const publicPaths = ['/login', '/register', '/forgot-password', '/reset-password', '/verify', '/'];
        const isPublicPath = publicPaths.includes(window.location.pathname);
        if (!isPublicPath) {
          window.location.href = '/login';
        }
      }
    }
    // Extract error details returned by FastAPI
    const message = error.response?.data?.detail || error.message || 'API request failed';
    const errObj = new Error(message) as any;
    errObj.status = error.response?.status;
    return Promise.reject(errObj);
  }
);

// ─── AUTH SERVICE ──────────────────────────────────────────────────────────
export const authService = {
  login: async (data: any) => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },
  register: async (data: any) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  updateProfile: async (data: any) => {
    const response = await api.put('/auth/me', data);
    return response.data;
  },
  changePassword: async (data: any) => {
    const response = await api.post('/auth/change-password', data);
    return response.data;
  }
};

// ─── COST SERVICE ──────────────────────────────────────────────────────────
export const costService = {
  getDashboard: async () => {
    const response = await api.get('/costs/dashboard');
    return response.data;
  },
  getBreakdown: async (start?: string, end?: string) => {
    const response = await api.get('/costs/breakdown', {
      params: { start_date: start, end_date: end }
    });
    return response.data;
  },
  getCosts: async (start?: string, end?: string, service?: string) => {
    const response = await api.get('/costs/', {
      params: { start_date: start, end_date: end, service }
    });
    return response.data;
  }
};

// ─── BUDGET SERVICE ────────────────────────────────────────────────────────
export const budgetService = {
  getBudgets: async () => {
    const response = await api.get('/budgets/');
    return response.data;
  },
  createBudget: async (data: any) => {
    const response = await api.post('/budgets/', data);
    return response.data;
  },
  updateBudget: async (id: string, data: any) => {
    const response = await api.put(`/budgets/${id}`, data);
    return response.data;
  },
  deleteBudget: async (id: string) => {
    const response = await api.delete(`/budgets/${id}`);
    return response.data;
  }
};

// ─── RECOMMENDATION SERVICE ────────────────────────────────────────────────
export const recommendationService = {
  getRecommendations: async () => {
    const response = await api.get('/recommendations/');
    return response.data;
  },
  getSummary: async () => {
    const response = await api.get('/recommendations/summary');
    return response.data;
  },
  getIdleResources: async () => {
    const response = await api.get('/recommendations/idle-resources');
    return response.data;
  },
  updateStatus: async (id: string, status: string) => {
    const response = await api.put(`/recommendations/${id}/status`, { status });
    return response.data;
  }
};

// ─── ANOMALY SERVICE ───────────────────────────────────────────────────────
export const anomalyService = {
  getAnomalies: async () => {
    const response = await api.get('/anomalies/');
    return response.data;
  },
  getSummary: async () => {
    const response = await api.get('/anomalies/summary');
    return response.data;
  },
  detect: async () => {
    const response = await api.post('/anomalies/detect');
    return response.data;
  }
};

// ─── AI SERVICE ────────────────────────────────────────────────────────────
const FINOPS_KB: Record<string, string> = {
  "reduce costs": "Here are top strategies to reduce AWS costs:\n1. **Right-size instances** — Match EC2/RDS instance types to actual workload needs\n2. **Use Reserved Instances / Savings Plans** — Commit for 1-3 years for 30-72% savings\n3. **Enable S3 Intelligent-Tiering** — Automatic storage class optimization\n4. **Delete idle resources** — Remove unattached EBS volumes, unused EIPs, idle load balancers\n5. **Schedule non-production workloads** — Stop dev/staging instances overnight\n6. **Use Spot Instances** — For fault-tolerant workloads, save up to 90%\n7. **Implement lifecycle policies** — Auto-archive old S3 objects to Glacier",
  "expensive service": "To find your most expensive AWS service, check the **Cost Analytics** page. Typically, the top cost drivers are:\n1. **Amazon EC2** (compute) — Usually 40-60% of total spend\n2. **Amazon RDS** (databases) — 15-25% of spend\n3. **Amazon S3** (storage) — 5-15% of spend\n4. **Data Transfer** — Often an overlooked cost driver",
  "ec2 spending": "EC2 spending can increase due to:\n- **Auto-scaling events** adding more instances\n- **Instance type changes** (upsizing)\n- **New deployments** or workload migrations\n- **Forgotten dev/test instances** running 24/7\n\nCheck the **Resource Optimizer** page for idle EC2 instances and rightsizing recommendations.",
  "predict": "I can predict your future AWS costs using time-series analysis. Check the **AI Insights** page for:\n- Next day forecast\n- Next week forecast\n- Next month forecast\n- Next quarter forecast\n\nForecasts include confidence intervals to show the range of expected spending.",
  "anomaly": "Cost anomalies are detected using Isolation Forest ML algorithm. When spending deviates significantly from normal patterns, we flag it with:\n- **Severity** (critical/high/medium/low)\n- **Impact amount** ($ deviation from baseline)\n- **Root cause analysis** (likely reason for the anomaly)\n\nCheck the **AI Insights** page for current anomalies.",
  "budget": "You can manage budgets from the **Budgets** page:\n- Create budgets with custom thresholds (50%, 80%, 90%, 100%)\n- Get alerts via email, dashboard, or SNS\n- Track spending vs. budget in real-time\n- Set daily, weekly, or monthly periods",
};

export const aiService = {
  getForecasts: async () => {
    const response = await api.get('/forecasts/');
    return response.data;
  },
  generateForecasts: async () => {
    const response = await api.post('/forecasts/generate');
    return response.data;
  },
  chat: async (message: string) => {
    const msgLower = message.toLowerCase().trim();
    
    // 1. Send message to backend AI chat endpoint
    try {
      const response = await api.post('/assistant/chat', { message });
      return response.data;
    } catch (err: any) {
      console.warn('Backend assistant chat call failed. Falling back to local rule-based response.', err);
    }

    // 2. Local high fidelity rule-based fallback response
    let responseText = "I can help you understand your cloud costs and find savings opportunities. Try asking about: cost reductions, EC2 spending, budget policies, anomaly detection or forecasts.";
    
    if (msgLower.includes('reduce') || msgLower.includes('save') || msgLower.includes('cut')) {
      responseText = FINOPS_KB['reduce costs'];
    } else if (msgLower.includes('expensive') || msgLower.includes('most cost') || msgLower.includes('highest')) {
      responseText = FINOPS_KB['expensive service'];
    } else if (msgLower.includes('ec2') || msgLower.includes('compute')) {
      responseText = FINOPS_KB['ec2 spending'];
    } else if (msgLower.includes('predict') || msgLower.includes('forecast') || msgLower.includes('future')) {
      responseText = FINOPS_KB['predict'];
    } else if (msgLower.includes('anomaly') || msgLower.includes('spike') || msgLower.includes('unusual')) {
      responseText = FINOPS_KB['anomaly'];
    } else if (msgLower.includes('budget') || msgLower.includes('alert')) {
      responseText = FINOPS_KB['budget'];
    } else if (msgLower.includes('hello') || msgLower.includes('hi') || msgLower.includes('hey')) {
      responseText = "👋 Hi! I'm your AI FinOps Assistant. I'm powered by Google Gemini. I can help you with bill analysis, cost reductions, anomaly scanning, and forecasting cloud spend. Ask me anything!";
    }

    return {
      response: responseText,
      source: 'knowledge_base',
      suggestions: ['How to reduce costs?', 'Show me EC2 tips', 'How are anomalies found?']
    };
  }
};

// ─── SETUP SERVICE ─────────────────────────────────────────────────────────
export const setupService = {
  health: async () => {
    const response = await api.get('/health');
    return response.data;
  },
  logFrontend: async (level: string, message: string, component?: string, stack?: string) => {
    try {
      await api.post('/logs/frontend', { level, message, component, stack });
    } catch (e) {
      console.error('Failed to report log to backend:', e);
    }
  }
};

// ─── REPORT SERVICE ────────────────────────────────────────────────────────
export const reportService = {
  getReports: async () => {
    const response = await api.get('/reports/');
    return response.data;
  },
  generateReport: async (data: { report_type: string; format: string }) => {
    const response = await api.post('/reports/generate', data);
    return response.data;
  },
  deleteReport: async (id: string) => {
    const response = await api.delete(`/reports/${id}`);
    return response.data;
  }
};

// ─── SETTINGS SERVICE ──────────────────────────────────────────────────────
export const settingsService = {
  getSettings: async () => {
    const response = await api.get('/settings/');
    return response.data;
  },
  updateSettings: async (data: any) => {
    const response = await api.put('/settings/', data);
    return response.data;
  },
  getAWSAccount: async () => {
    const response = await api.get('/settings/aws');
    return response.data;
  },
  updateAWSAccount: async (data: any) => {
    const response = await api.put('/settings/aws', data);
    return response.data;
  }
};

// ─── AUDIT SERVICE ─────────────────────────────────────────────────────────
export const auditService = {
  getAuditLogs: async (page = 1, pageSize = 20) => {
    const response = await api.get('/audit-logs/', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }
};
