import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize Simulated Local Storage Database
const seedLocalStorage = () => {
  if (!localStorage.getItem('cw_user')) {
    localStorage.setItem('cw_user', JSON.stringify({
      id: 'usr_mock123',
      email: 'user@example.com',
      full_name: 'CloudWise User',
      role: 'USER',
      account_status: 'active',
      is_demo_mode: true,
      is_aws_connected: true,
      org_id: 'org_mock123'
    }));
  }

  if (!localStorage.getItem('cw_aws_account')) {
    localStorage.setItem('cw_aws_account', JSON.stringify({
      account_id: '123456789012',
      role_arn: 'arn:aws:iam::123456789012:role/CloudWiseCostOptimizerRole',
      status: 'connected',
      connected_at: new Date().toISOString()
    }));
  }

  if (!localStorage.getItem('cw_settings')) {
    localStorage.setItem('cw_settings', JSON.stringify({
      theme: 'dark',
      email_alerts: true,
      weekly_reports: true,
      slack_webhook_url: 'https://hooks.slack.com/services/mock/web/hook',
      threshold_multiplier: 1.5
    }));
  }

  if (!localStorage.getItem('cw_budgets')) {
    localStorage.setItem('cw_budgets', JSON.stringify([
      {
        id: 'bdg_1',
        name: 'EC2 Compute Limit',
        amount: 2500,
        spent: 2145.5,
        currency: 'USD',
        period: 'monthly',
        thresholds: [50, 80, 90, 100],
        created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString()
      },
      {
        id: 'bdg_2',
        name: 'RDS Databases',
        amount: 1500,
        spent: 982.3,
        currency: 'USD',
        period: 'monthly',
        thresholds: [50, 80, 90, 100],
        created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString()
      },
      {
        id: 'bdg_3',
        name: 'S3 Cold Storage',
        amount: 800,
        spent: 521.8,
        currency: 'USD',
        period: 'monthly',
        thresholds: [50, 80, 100],
        created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString()
      }
    ]));
  }

  const recsStr = localStorage.getItem('cw_recommendations');
  if (!recsStr || !recsStr.includes('resource_type')) {
    localStorage.setItem('cw_recommendations', JSON.stringify([
      {
        id: 'rec_1',
        resource_type: 'EC2 Instance',
        resource_id: 'i-08a7b6c5d4e3f21a0',
        priority: 'high',
        category: 'Rightsizing',
        recommendation: 'Downgrade 4 idle EC2 t3.xlarge instances to t3.medium in dev environment.',
        current_cost: 120.0,
        optimized_cost: 35.0,
        monthly_savings: 85.0,
        status: 'pending'
      },
      {
        id: 'rec_2',
        resource_type: 'RDS Instance',
        resource_id: 'rds-db-prod-replica',
        priority: 'medium',
        category: 'Rightsizing',
        recommendation: 'Upgrade DB from db.m5.xlarge to db.m6g.large for better Graviton performance.',
        current_cost: 280.0,
        optimized_cost: 160.0,
        monthly_savings: 120.0,
        status: 'pending'
      },
      {
        id: 'rec_3',
        resource_type: 'S3 Bucket',
        resource_id: 's3-logs-compliance-backups',
        priority: 'low',
        category: 'Storage Optimization',
        recommendation: 'Configure S3 lifecycle rules to move backups older than 90 days to Glacier.',
        current_cost: 75.0,
        optimized_cost: 30.0,
        monthly_savings: 45.0,
        status: 'pending'
      },
      {
        id: 'rec_4',
        resource_type: 'EBS Volume',
        resource_id: 'vol-0bcde123456789abc',
        priority: 'medium',
        category: 'Idle Resource',
        recommendation: 'Delete gp2 EBS volume unattached for more than 30 days.',
        current_cost: 30.0,
        optimized_cost: 0.0,
        monthly_savings: 30.0,
        status: 'pending'
      }
    ]));
  }

  if (!localStorage.getItem('cw_anomalies')) {
    localStorage.setItem('cw_anomalies', JSON.stringify([
      {
        id: 'anm_1',
        service: 'Amazon EC2',
        date: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString().split('T')[0],
        severity: 'high',
        impact_amount: 240.0,
        root_cause: 'Unplanned scale-out event in Auto Scaling Group (asg-prod-compute).',
        details: 'A Jenkins batch job triggered redundant instances that ran continuously for 48 hours.',
        is_resolved: false
      },
      {
        id: 'anm_2',
        service: 'Amazon S3',
        date: new Date(Date.now() - 10 * 24 * 3600 * 1000).toISOString().split('T')[0],
        severity: 'medium',
        impact_amount: 95.0,
        root_cause: 'Data egress spike from backups bucket.',
        details: 'A third-party compliance verification tool pulled raw server database logs twice instead of once.',
        is_resolved: false
      }
    ]));
  }
  const reportsStr = localStorage.getItem('cw_reports');
  if (!reportsStr || !reportsStr.includes('filename')) {
    localStorage.setItem('cw_reports', JSON.stringify([
      {
        id: 'rep_1',
        name: 'Cost_Summary_June_2026',
        filename: 'Cost_Summary_June_2026.pdf',
        report_type: 'executive_summary',
        format: 'pdf',
        status: 'completed',
        created_at: new Date(Date.now() - 12 * 24 * 3600 * 1000).toISOString(),
        size: '1.2 MB'
      },
      {
        id: 'rep_2',
        name: 'Idle_Resources_Q2_2026',
        filename: 'Idle_Resources_Q2_2026.xlsx',
        report_type: 'resource_optimization',
        format: 'xlsx',
        status: 'completed',
        created_at: new Date(Date.now() - 4 * 24 * 3600 * 1000).toISOString(),
        size: '856 KB'
      }
    ]));
  }
};

// Seed initial state
seedLocalStorage();

// Constants
export const BACKEND_URL = '/api/v1';

// Helper for simulation latencies
const delay = (ms = 150) => new Promise(resolve => setTimeout(resolve, ms));

// Generate realistic cost data
const generateDailyCosts = () => {
  const dailyCosts = [];
  const baseDate = new Date();
  baseDate.setDate(baseDate.getDate() - 30);
  
  // Deterministic but dynamic noise
  for (let i = 0; i < 30; i++) {
    const dateStr = new Date(baseDate).toISOString().split('T')[0];
    const dayOfWeek = baseDate.getDay();
    // Weekends are cheaper
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    const baseValue = isWeekend ? 115 : 155;
    const noise = Math.sin(i * 0.8) * 15 + Math.cos(i * 0.5) * 8;
    
    dailyCosts.push({
      date: dateStr,
      amount: Math.round((baseValue + noise) * 100) / 100
    });
    baseDate.setDate(baseDate.getDate() + 1);
  }
  return dailyCosts;
};

// ─── AUTH SERVICE ──────────────────────────────────────────────────────────
export const authService = {
  login: async (data: any) => {
    await delay(300);
    // Find or simulate user
    const user = {
      id: 'usr_mock123',
      email: data.email || 'user@example.com',
      full_name: data.email?.split('@')[0]?.toUpperCase() || 'CloudWise User',
      role: 'USER' as const,
      account_status: 'active',
      is_demo_mode: true,
      is_aws_connected: true,
      org_id: 'org_mock123'
    };
    localStorage.setItem('access_token', 'mock-token-12345');
    localStorage.setItem('cw_user', JSON.stringify(user));
    return { access_token: 'mock-token-12345', token_type: 'bearer', user };
  },
  register: async (data: any) => {
    await delay(400);
    const user = {
      id: 'usr_mock' + Math.random().toString(36).substring(2, 7),
      email: data.email,
      full_name: data.full_name,
      role: 'USER' as const,
      account_status: 'active',
      is_demo_mode: true,
      is_aws_connected: true,
      org_id: 'org_mock' + Math.random().toString(36).substring(2, 7)
    };
    localStorage.setItem('access_token', 'mock-token-12345');
    localStorage.setItem('cw_user', JSON.stringify(user));
    return { access_token: 'mock-token-12345', token_type: 'bearer', user };
  },
  getProfile: async () => {
    await delay(100);
    const userStr = localStorage.getItem('cw_user');
    if (!userStr) throw new Error('Not authenticated');
    return JSON.parse(userStr);
  },
  updateProfile: async (data: any) => {
    await delay(200);
    const userStr = localStorage.getItem('cw_user');
    if (!userStr) throw new Error('Not authenticated');
    const user = JSON.parse(userStr);
    const updated = { ...user, full_name: data.full_name, email: data.email };
    localStorage.setItem('cw_user', JSON.stringify(updated));
    return updated;
  },
  changePassword: async (_data: any) => {
    await delay(300);
    return { message: 'Password updated successfully' };
  }
};

// ─── COST SERVICE ──────────────────────────────────────────────────────────
export const costService = {
  getDashboard: async () => {
    await delay(200);
    const dailyCosts = generateDailyCosts();
    const totalSpend = dailyCosts.reduce((acc, curr) => acc + curr.amount, 0);
    
    // Unresolved anomalies from local storage
    const anomalies = JSON.parse(localStorage.getItem('cw_anomalies') || '[]');
    const activeCount = anomalies.filter((a: any) => !a.is_resolved).length;

    return {
      total_spend_mtd: Math.round(totalSpend * 100) / 100,
      total_spend_prev_month: 3892.40,
      spend_change_pct: 11.8,
      daily_spend_avg: Math.round((totalSpend / 30) * 100) / 100,
      forecasted_month_end: Math.round((totalSpend * 1.08) * 100) / 100,
      active_anomalies: activeCount,
      daily_costs: dailyCosts,
      top_services: [
        { service: 'Amazon EC2', amount: 2145.5, percentage: 49.3 },
        { service: 'Amazon RDS', amount: 982.3, percentage: 22.6 },
        { service: 'Amazon S3', amount: 521.8, percentage: 12.0 },
        { service: 'AWS Lambda', amount: 321.4, percentage: 7.4 },
        { service: 'Amazon CloudFront', amount: 381.8, percentage: 8.7 }
      ]
    };
  },
  getBreakdown: async (start?: string, end?: string) => {
    await delay(150);
    return {
      by_service: [
        { service: 'Amazon EC2', amount: 2145.5, percentage: 49.3 },
        { service: 'Amazon RDS', amount: 982.3, percentage: 22.6 },
        { service: 'Amazon S3', amount: 521.8, percentage: 12.0 },
        { service: 'AWS Lambda', amount: 321.4, percentage: 7.4 },
        { service: 'Amazon CloudFront', amount: 381.8, percentage: 8.7 }
      ],
      by_region: [
        { region: 'us-east-1', amount: 2835.40, percentage: 65.1 },
        { region: 'us-west-2', amount: 1088.20, percentage: 25.0 },
        { region: 'eu-west-1', amount: 429.20, percentage: 9.9 }
      ]
    };
  },
  getCosts: async (_start?: string, _end?: string, _service?: string) => {
    await delay(150);
    const dailyCosts = generateDailyCosts();
    const services = ['Amazon EC2', 'Amazon RDS', 'Amazon S3', 'AWS Lambda', 'Amazon CloudFront'];
    const distribution = [0.49, 0.23, 0.12, 0.07, 0.09];
    
    const records: any[] = [];
    dailyCosts.forEach(d => {
      services.forEach((service, index) => {
        if (!_service || _service === 'All Services' || _service === service) {
          records.push({
            date: d.date,
            service: service,
            amount: Math.round(d.amount * distribution[index] * 100) / 100
          });
        }
      });
    });
    return records;
  }
};

// ─── BUDGET SERVICE ────────────────────────────────────────────────────────
export const budgetService = {
  getBudgets: async () => {
    await delay(100);
    return JSON.parse(localStorage.getItem('cw_budgets') || '[]');
  },
  createBudget: async (data: any) => {
    await delay(200);
    const budgets = JSON.parse(localStorage.getItem('cw_budgets') || '[]');
    const newBudget = {
      id: 'bdg_' + Math.random().toString(36).substring(2, 7),
      name: data.name,
      amount: parseFloat(data.amount),
      spent: 0,
      currency: 'USD',
      period: data.period || 'monthly',
      thresholds: data.thresholds || [50, 80, 100],
      created_at: new Date().toISOString()
    };
    budgets.push(newBudget);
    localStorage.setItem('cw_budgets', JSON.stringify(budgets));
    return newBudget;
  },
  updateBudget: async (id: string, data: any) => {
    await delay(200);
    const budgets = JSON.parse(localStorage.getItem('cw_budgets') || '[]');
    const index = budgets.findIndex((b: any) => b.id === id);
    if (index === -1) throw new Error('Budget not found');
    budgets[index] = {
      ...budgets[index],
      name: data.name,
      amount: parseFloat(data.amount),
      period: data.period || budgets[index].period,
      thresholds: data.thresholds || budgets[index].thresholds
    };
    localStorage.setItem('cw_budgets', JSON.stringify(budgets));
    return budgets[index];
  },
  deleteBudget: async (id: string) => {
    await delay(200);
    const budgets = JSON.parse(localStorage.getItem('cw_budgets') || '[]');
    const filtered = budgets.filter((b: any) => b.id !== id);
    localStorage.setItem('cw_budgets', JSON.stringify(filtered));
    return { success: true };
  }
};

// ─── RECOMMENDATION SERVICE ────────────────────────────────────────────────
export const recommendationService = {
  getRecommendations: async () => {
    await delay(150);
    return JSON.parse(localStorage.getItem('cw_recommendations') || '[]');
  },
  getSummary: async () => {
    await delay(100);
    const recs = JSON.parse(localStorage.getItem('cw_recommendations') || '[]');
    const pendingRecs = recs.filter((r: any) => r.status === 'pending');
    const totalSavings = pendingRecs.reduce((acc: number, curr: any) => acc + curr.savings, 0);
    return {
      total_recommendations: pendingRecs.length,
      total_monthly_savings: Math.round(totalSavings * 100) / 100
    };
  },
  getIdleResources: async () => {
    await delay(150);
    return [
      { id: 'idl_1', name: 'dev-sandbox-ec2', resource_type: 'Instance', service: 'Amazon EC2', status: 'stopped', idle_days: 14, monthly_waste: 24.5 },
      { id: 'idl_2', name: 'temp-logs-backup', resource_type: 'Bucket', service: 'Amazon S3', status: 'active', idle_days: 42, monthly_waste: 15.0 },
      { id: 'idl_3', name: 'unattached-vol-a', resource_type: 'Volume', service: 'EBS', status: 'available', idle_days: 30, monthly_waste: 12.0 }
    ];
  },
  updateStatus: async (id: string, status: string) => {
    await delay(200);
    const recs = JSON.parse(localStorage.getItem('cw_recommendations') || '[]');
    const index = recs.findIndex((r: any) => r.id === id);
    if (index === -1) throw new Error('Recommendation not found');
    recs[index].status = status;
    localStorage.setItem('cw_recommendations', JSON.stringify(recs));
    return recs[index];
  }
};

// ─── ANOMALY SERVICE ───────────────────────────────────────────────────────
export const anomalyService = {
  getAnomalies: async () => {
    await delay(150);
    return JSON.parse(localStorage.getItem('cw_anomalies') || '[]');
  },
  getSummary: async () => {
    await delay(100);
    const anomalies = JSON.parse(localStorage.getItem('cw_anomalies') || '[]');
    const active = anomalies.filter((a: any) => !a.is_resolved);
    const impact = active.reduce((acc: number, curr: any) => acc + curr.impact_amount, 0);
    return {
      active_anomalies_count: active.length,
      total_financial_impact: Math.round(impact * 100) / 100
    };
  },
  detect: async () => {
    await delay(2500); // Simulate ML Scan latency
    const anomalies = JSON.parse(localStorage.getItem('cw_anomalies') || '[]');
    
    // Add a new anomaly if none was generated recently
    const hasLatest = anomalies.some((a: any) => a.date === new Date().toISOString().split('T')[0]);
    if (!hasLatest) {
      const newAnomaly = {
        id: 'anm_' + Math.random().toString(36).substring(2, 7),
        service: 'AWS Lambda',
        date: new Date().toISOString().split('T')[0],
        severity: 'low' as const,
        impact_amount: 32.40,
        root_cause: 'Execution timeout storm due to downstream database lock.',
        details: 'Function (invoice-pdf-generator) was repeatedly retried due to DB lock, exceeding standard run budget.',
        is_resolved: false
      };
      anomalies.unshift(newAnomaly);
      localStorage.setItem('cw_anomalies', JSON.stringify(anomalies));
      return { status: 'completed', anomalies_found: 1, new_anomalies: [newAnomaly] };
    }
    return { status: 'completed', anomalies_found: 0, new_anomalies: [] };
  }
};

// ─── AI SERVICE ────────────────────────────────────────────────────────────
// Pre-built rule-based chatbot replies if direct Gemini API keys are missing.
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
    await delay(150);
    return {
      next_day: { predicted_amount: 145.2, confidence_interval: [135, 155] },
      next_week: { predicted_amount: 1025.4, confidence_interval: [980, 1070] },
      next_month: { predicted_amount: 4498.1, confidence_interval: [4350, 4650] },
      next_quarter: { predicted_amount: 13580.0, confidence_interval: [12900, 14200] },
      daily_predictions: Array.from({ length: 30 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i);
        return {
          date: d.toISOString().split('T')[0],
          predicted_amount: Math.round((145 + Math.sin(i * 0.5) * 8) * 100) / 100
        };
      })
    };
  },
  generateForecasts: async () => {
    await delay(1200);
    return { success: true };
  },
  chat: async (message: string) => {
    await delay(500);
    const msgLower = message.toLowerCase().trim();
    
    // Verify direct Gemini SDK availability
    const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
    if (apiKey && apiKey !== 'your_gemini_api_key_here' && apiKey.trim() !== '') {
      try {
        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
        const systemPrompt = (
          "You are CloudWise AI, an expert FinOps assistant specializing in AWS cost optimization and cloud economics. " +
          "Provide concise, actionable advice about AWS billing, cost optimization, rightsizing, and cloud architecture. " +
          "Use clear markdown formatting. Be specific with AWS service names and pricing details."
        );
        const result = await model.generateContent(`${systemPrompt}\n\nUser Question: ${message}`);
        const response = await result.response;
        return {
          response: response.text().trim(),
          source: 'gemini_ai',
          suggestions: ['How can I reduce EC2 costs?', 'Explain S3 lifecycle rules', 'How are budgets monitored?']
        };
      } catch (err: any) {
        console.error('Direct Google Gemini API call failed:', err);
      }
    }

    // High fidelity rule-based fallback response
    let response = "I can help you understand your cloud costs and find savings opportunities. Try asking about: cost reductions, EC2 spending, budget policies, anomaly detection or forecasts.";
    
    if (msgLower.includes('reduce') || msgLower.includes('save') || msgLower.includes('cut')) {
      response = FINOPS_KB['reduce costs'];
    } else if (msgLower.includes('expensive') || msgLower.includes('most cost') || msgLower.includes('highest')) {
      response = FINOPS_KB['expensive service'];
    } else if (msgLower.includes('ec2') || msgLower.includes('compute')) {
      response = FINOPS_KB['ec2 spending'];
    } else if (msgLower.includes('predict') || msgLower.includes('forecast') || msgLower.includes('future')) {
      response = FINOPS_KB['predict'];
    } else if (msgLower.includes('anomaly') || msgLower.includes('spike') || msgLower.includes('unusual')) {
      response = FINOPS_KB['anomaly'];
    } else if (msgLower.includes('budget') || msgLower.includes('alert')) {
      response = FINOPS_KB['budget'];
    } else if (msgLower.includes('hello') || msgLower.includes('hi') || msgLower.includes('hey')) {
      response = "👋 Hi! I'm your AI FinOps Assistant. I'm powered by Google Gemini. I can help you with bill analysis, cost reductions, anomaly scanning, and forecasting cloud spend. Ask me anything!";
    }

    return {
      response,
      source: 'knowledge_base',
      suggestions: ['How to reduce costs?', 'Show me EC2 tips', 'How are anomalies found?']
    };
  }
};

// ─── SETUP SERVICE ─────────────────────────────────────────────────────────
export const setupService = {
  health: async () => {
    return { status: 'healthy', database: 'connected', version: '1.0.0-mock' };
  }
};

// ─── REPORT SERVICE ────────────────────────────────────────────────────────
export const reportService = {
  getReports: async () => {
    await delay(100);
    return JSON.parse(localStorage.getItem('cw_reports') || '[]');
  },
  generateReport: async (data: { report_type: string; format: string }) => {
    await delay(1500); // Simulate PDF generation delay
    const reports = JSON.parse(localStorage.getItem('cw_reports') || '[]');
    const reportNames: Record<string, string> = {
      executive_summary: 'Cost_Executive_Summary_',
      resource_optimization: 'Idle_Resources_Report_',
      billing_anomaly: 'Anomaly_Audit_Report_'
    };
    const newReport = {
      id: 'rep_' + Math.random().toString(36).substring(2, 7),
      name: (reportNames[data.report_type] || 'Report_') + new Date().toISOString().split('T')[0],
      filename: (reportNames[data.report_type] || 'Report_') + new Date().toISOString().split('T')[0] + '.' + data.format,
      report_type: data.report_type,
      format: data.format,
      status: 'completed',
      created_at: new Date().toISOString(),
      size: data.format === 'pdf' ? '1.1 MB' : '480 KB'
    };
    reports.unshift(newReport);
    localStorage.setItem('cw_reports', JSON.stringify(reports));
    return newReport;
  },
  deleteReport: async (id: string) => {
    await delay(150);
    const reports = JSON.parse(localStorage.getItem('cw_reports') || '[]');
    const filtered = reports.filter((r: any) => r.id !== id);
    localStorage.setItem('cw_reports', JSON.stringify(filtered));
    return { success: true };
  }
};

// ─── SETTINGS SERVICE ──────────────────────────────────────────────────────
export const settingsService = {
  getSettings: async () => {
    await delay(100);
    return JSON.parse(localStorage.getItem('cw_settings') || '{}');
  },
  updateSettings: async (data: any) => {
    await delay(200);
    localStorage.setItem('cw_settings', JSON.stringify(data));
    return data;
  },
  getAWSAccount: async () => {
    await delay(100);
    return JSON.parse(localStorage.getItem('cw_aws_account') || '{}');
  },
  updateAWSAccount: async (data: any) => {
    await delay(300);
    const account = {
      account_id: data.account_id,
      role_arn: data.role_arn,
      status: 'connected',
      connected_at: new Date().toISOString()
    };
    localStorage.setItem('cw_aws_account', JSON.stringify(account));
    
    // Set user AWS connected state
    const userStr = localStorage.getItem('cw_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      user.is_aws_connected = true;
      localStorage.setItem('cw_user', JSON.stringify(user));
    }
    
    return account;
  }
};

// ─── AUDIT SERVICE ─────────────────────────────────────────────────────────
export const auditService = {
  getAuditLogs: async (_page = 1, _pageSize = 20) => {
    await delay(100);
    return {
      items: [
        { id: 'aud_1', created_at: new Date(Date.now() - 3600 * 1000).toISOString(), action: 'login', resource_type: 'user', description: 'User login from IP 192.168.1.5', ip_address: '192.168.1.5' },
        { id: 'aud_2', created_at: new Date(Date.now() - 4 * 3600 * 1000).toISOString(), action: 'create', resource_type: 'budget', description: 'Created EC2 budget plan', ip_address: '192.168.1.5' },
        { id: 'aud_3', created_at: new Date(Date.now() - 1 * 24 * 3600 * 1000).toISOString(), action: 'update', resource_type: 'aws_integration', description: 'Updated AWS role ARN permissions config', ip_address: '192.168.1.5' }
      ]
    };
  }
};
