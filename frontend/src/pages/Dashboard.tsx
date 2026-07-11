import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell, Legend
} from 'recharts';
import { DollarSign, TrendingDown, Target, AlertTriangle } from 'lucide-react';
import { costService, aiService, recommendationService } from '../services/api';
import MetricCard from '../components/ui/MetricCard';
import Badge from '../components/ui/Badge';
import { formatCurrency } from '../lib/utils';
import { Skeleton, SkeletonCard } from '../components/ui/Skeleton';
import useStore from '../store';
import PageTransition from '../components/layout/PageTransition';
import { motion } from 'framer-motion';
import ErrorState from '../components/ui/ErrorState';
import { Card } from '../components/ui/Card';
import { DashboardDataCube } from '../components/3d/Internal3DElements';

import AWSOnboardingState from '../components/ui/AWSOnboardingState';
import AWSErrorState from '../components/ui/AWSErrorState';

const COLORS = ['#3b82f6', '#06b6d4', '#22c55e', '#f59e0b', '#ef4444'];

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [recs, setRecs] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [hasAWSError, setHasAWSError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const { theme, user } = useStore();
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    if (user && !user.is_demo_mode && !user.is_aws_connected) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setHasAWSError(false);
    try {
      const [dashboardData, forecastData, recData] = await Promise.all([
        costService.getDashboard(),
        aiService.getForecasts(),
        recommendationService.getSummary()
      ]);
      setMetrics(dashboardData);
      setForecast(forecastData);
      setRecs(recData);
      setLastUpdated(
        new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + 
        ', ' + 
        new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      );
    } catch (error: any) {
      console.error("Failed to load dashboard data:", error);
      if (error.message && (error.message.includes("AWS_ERROR") || error.message.includes("AWS") || error.message.includes("credentials") || error.message.includes("502"))) {
        setHasAWSError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Skeleton className="h-[400px] w-full rounded-xl" />
          </div>
          <Skeleton className="h-[400px] w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (user && !user.is_demo_mode && !user.is_aws_connected) {
    return <AWSOnboardingState />;
  }

  if (hasAWSError) {
    return <AWSErrorState onRetry={loadData} isLoading={loading} />;
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center min-h-[400px] p-6">
        <ErrorState 
          title="Data Connection Error"
          message="We couldn't load the cloud metrics from the server. Check your backend status or retry."
          onRetry={loadData}
        />
      </div>
    );
  }

  const areaData = (metrics?.daily_costs || []).map((d: any) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    amount: d.amount
  }));

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  // Generate helper sparkline data arrays based on available metrics
  const spendSparkline = areaData.length > 5 
    ? areaData.map((d: any) => d.amount) 
    : [210, 225, 200, 215, 230, 220, 240];
  const forecastSparkline = [
    metrics?.total_spend_mtd || 200, 
    (metrics?.total_spend_mtd || 200) * 1.05, 
    (metrics?.forecasted_month_end || 240) * 0.95, 
    metrics?.forecasted_month_end || 240
  ];
  const savingsSparkline = [
    (recs?.total_monthly_savings || 150) * 1.25, 
    (recs?.total_monthly_savings || 150) * 1.15, 
    (recs?.total_monthly_savings || 150) * 1.05, 
    recs?.total_monthly_savings || 150
  ];
  const anomalySparkline = metrics?.active_anomalies > 0 
    ? [0, 0, 1, 0, 1, metrics.active_anomalies] 
    : [0, 0, 0, 0, 0, 0];

  return (
    <PageTransition>
      <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative">
        <div className="relative z-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Executive Summary</h2>
          <p className="text-text-secondary text-sm">AI-driven insights into your cloud spending and optimization opportunities.</p>
        </div>
        <DashboardDataCube />
        {lastUpdated && (
          <div className="text-xs text-text-muted bg-background-secondary px-3 py-1.5 rounded-lg border border-border-primary shadow-sm relative z-10">
            Last updated: {lastUpdated}
          </div>
        )}
      </div>

      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={itemVariants}>
          <MetricCard
            title="Month-to-Date Spend"
            value={metrics?.total_spend_mtd || 0}
            change={metrics?.spend_change_pct || 0}
            icon={<DollarSign size={24} />}
            iconColor="purple"
            sparklineData={spendSparkline}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard
            title="Forecasted Month End"
            value={metrics?.forecasted_month_end || 0}
            change={((metrics?.forecasted_month_end || 0) - (metrics?.total_spend_prev_month || 1)) / (metrics?.total_spend_prev_month || 1) * 100}
            icon={<Target size={24} />}
            iconColor="blue"
            sparklineData={forecastSparkline}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard
            title="Savings Opportunity"
            value={recs?.total_monthly_savings || 0}
            change={-15.4}
            trend="down"
            icon={<TrendingDown size={24} />}
            iconColor="green"
            sparklineData={savingsSparkline}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard
            title="Active Anomalies"
            value={metrics?.active_anomalies || 0}
            type="number"
            change={metrics?.active_anomalies > 0 ? 100 : 0}
            trend={metrics?.active_anomalies > 0 ? "up" : "neutral"}
            icon={<AlertTriangle size={24} />}
            iconColor={metrics?.active_anomalies > 0 ? "red" : "green"}
            sparklineData={anomalySparkline}
          />
        </motion.div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Spending Trend */}
        <Card className="p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-xs font-bold tracking-wider text-text-muted uppercase">30-Day Spending Trend</h3>
          </div>
          <div className="h-[300px] w-full min-h-[300px]">
            <ResponsiveContainer width="100%" height={300} minWidth={0}>
              <AreaChart data={areaData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.05)'} />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 500 }} />
                <YAxis tickLine={false} axisLine={false} tickFormatter={(value) => `$${value}`} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 500 }} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-elevated)', borderColor: 'var(--border-primary)', borderRadius: '12px', boxShadow: 'var(--shadow-premium)' }}
                  labelStyle={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: '600', marginBottom: '4px' }}
                  itemStyle={{ color: 'var(--accent-primary)', fontSize: '12px', fontWeight: '500' }}
                  formatter={(value: any) => [formatCurrency(value as number), 'Spend']}
                />
                <Area type="monotone" dataKey="amount" stroke="var(--accent-primary)" strokeWidth={2.5} fillOpacity={1} fill="url(#colorAmount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* AI Insights Preview */}
        <Card className="p-5 flex flex-col">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-xs font-bold tracking-wider text-text-muted uppercase">AI Action Items</h3>
            <button aria-label="View all AI action items" className="text-accent-primary hover:text-accent-hover text-xs font-semibold transition-colors cursor-pointer" onClick={() => navigate('/ai-insights')}>View All</button>
          </div>
          <div className="flex-1 overflow-y-auto pr-1 space-y-3">
            {forecast?.next_month && (
              <div 
                className="cursor-pointer p-4 rounded-xl border border-border-primary bg-background-primary/40 hover:bg-background-elevated transition-all flex flex-col gap-2 group shadow-sm"
                onClick={() => navigate('/ai-insights')}
              >
                <div className="flex items-center justify-between">
                  <Badge variant="info">Forecast</Badge>
                  <Badge variant="healthy" showIcon={false}>Active</Badge>
                </div>
                <p className="text-xs text-text-primary font-medium leading-relaxed group-hover:text-accent-primary transition-colors">
                  Next month spending projected to be {formatCurrency(forecast.next_month.predicted_amount)}
                </p>
              </div>
            )}
            {metrics?.active_anomalies > 0 && (
              <div 
                className="cursor-pointer p-4 rounded-xl border border-border-primary bg-background-primary/40 hover:bg-background-elevated transition-all flex flex-col gap-2 group shadow-sm"
                onClick={() => navigate('/analytics')}
              >
                <div className="flex items-center justify-between">
                  <Badge variant="critical">Anomaly</Badge>
                  <Badge variant="critical" showIcon={false}>Unresolved</Badge>
                </div>
                <p className="text-xs text-text-primary font-medium leading-relaxed group-hover:text-danger transition-colors">
                  Detected {metrics?.active_anomalies} unhandled anomalies
                </p>
              </div>
            )}
            {recs && recs.total_recommendations > 0 && (
              <div 
                className="cursor-pointer p-4 rounded-xl border border-border-primary bg-background-primary/40 hover:bg-background-elevated transition-all flex flex-col gap-2 group shadow-sm"
                onClick={() => navigate('/resources')}
              >
                <div className="flex items-center justify-between">
                  <Badge variant="warning">Optimization</Badge>
                  <Badge variant="pending" showIcon={false}>Pending</Badge>
                </div>
                <p className="text-xs text-text-primary font-medium leading-relaxed group-hover:text-warning transition-colors">
                  Found {recs.total_recommendations} new cost optimization opportunities
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Top Services */}
        <Card className="p-5 lg:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold tracking-wider text-text-muted uppercase">Top Services</h3>
          </div>
          <div className="h-[280px] w-full flex items-center justify-center min-h-[280px]">
            <ResponsiveContainer width="100%" height={280} minWidth={0}>
              <PieChart>
                <Pie
                  data={(metrics?.top_services || []).slice(0, 5)}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="amount"
                  nameKey="service"
                  stroke="none"
                >
                  {(metrics?.top_services || []).slice(0, 5).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-elevated)', borderColor: 'var(--border-primary)', borderRadius: '12px', boxShadow: 'var(--shadow-premium)' }}
                  itemStyle={{ color: 'var(--text-primary)', fontSize: '11px', fontWeight: '500' }}
                  formatter={(value: any) => [formatCurrency(value as number)]}
                />
                <Legend layout="vertical" verticalAlign="middle" align="right" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </PageTransition>
  );
}
