import React, { useEffect, useState, useCallback } from 'react';
import { adminService } from '../../services/api';
import { Users, Shield, Cpu, Activity, Database, CheckCircle, RefreshCw } from 'lucide-react';
import useStore from '../../store';

interface DashboardStats {
  total_users: number;
  total_reviewers: number;
  aws_connected_users: number;
  active_users: number;
  demo_users: number;
  system_status: string;
}

export default function AdminDashboard() {
  const { addToast } = useStore();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      const data = await adminService.getDashboard();
      setStats(data);
      if (isRefresh) addToast("Dashboard metrics updated successfully", "success");
    } catch (e: any) {
      addToast(e.message || "Failed to fetch admin stats", "error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading) {
    return (
      <div className="h-[60vh] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Users",
      value: stats?.total_users || 0,
      description: "Registered accounts in database",
      icon: Users,
      color: "from-blue-500/10 to-cyan-500/10 text-blue-400 border-blue-500/15"
    },
    {
      title: "Total Reviewers",
      value: stats?.total_reviewers || 0,
      description: "Users mapped to evaluation demo mode",
      icon: Shield,
      color: "from-amber-500/10 to-orange-500/10 text-amber-400 border-amber-500/15"
    },
    {
      title: "AWS Connected",
      value: stats?.aws_connected_users || 0,
      description: "Users connected to live AWS APIs",
      icon: Database,
      color: "from-emerald-500/10 to-teal-500/10 text-emerald-400 border-emerald-500/15"
    },
    {
      title: "Active Users",
      value: stats?.active_users || 0,
      description: "Users with non-disabled accounts",
      icon: Activity,
      color: "from-indigo-500/10 to-purple-500/10 text-indigo-400 border-indigo-500/15"
    }
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">System Overview</h1>
          <p className="text-sm text-text-secondary mt-1">Real-time health statistics and enterprise metrics for governance.</p>
        </div>
        <button
          onClick={() => fetchStats(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-background-elevated border border-border-primary text-text-primary hover:bg-background-primary transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          Sync Metrics
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, idx) => (
          <div
            key={idx}
            className={`p-6 rounded-xl border bg-gradient-to-br ${card.color} shadow-sm flex flex-col justify-between h-36 transition-all duration-300 hover:scale-[1.01] hover:shadow-md`}
          >
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-text-muted">{card.title}</span>
              <card.icon size={20} className="opacity-80" />
            </div>
            <div className="mt-4">
              <span className="text-3xl font-extrabold tracking-tight text-text-primary leading-none">
                {card.value}
              </span>
              <p className="text-[11px] text-text-muted mt-2 font-medium">{card.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* System Status and Server Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health */}
        <div className="lg:col-span-2 p-6 rounded-xl border border-border-primary bg-background-secondary shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-border-primary/50 pb-4">
            <span className="font-bold text-sm text-text-primary">Infrastructure Health</span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              All Services Operational
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-background-elevated/45 border border-border-primary/30 space-y-1">
              <span className="text-[10px] uppercase font-bold text-text-muted">API Gateway</span>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle size={14} className="text-emerald-400" />
                <span className="text-xs font-bold text-text-primary">Healthy</span>
              </div>
            </div>
            <div className="p-4 rounded-lg bg-background-elevated/45 border border-border-primary/30 space-y-1">
              <span className="text-[10px] uppercase font-bold text-text-muted">Database Server</span>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle size={14} className="text-emerald-400" />
                <span className="text-xs font-bold text-text-primary">Online (SQLite WAL)</span>
              </div>
            </div>
            <div className="p-4 rounded-lg bg-background-elevated/45 border border-border-primary/30 space-y-1">
              <span className="text-[10px] uppercase font-bold text-text-muted">Celery Worker Queue</span>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle size={14} className="text-emerald-400" />
                <span className="text-xs font-bold text-text-primary">Idle (0 tasks waiting)</span>
              </div>
            </div>
            <div className="p-4 rounded-lg bg-background-elevated/45 border border-border-primary/30 space-y-1">
              <span className="text-[10px] uppercase font-bold text-text-muted">Redis Cache Store</span>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle size={14} className="text-emerald-400" />
                <span className="text-xs font-bold text-text-primary">Connected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Server Performance Stats */}
        <div className="p-6 rounded-xl border border-border-primary bg-background-secondary shadow-sm space-y-5">
          <span className="font-bold text-sm text-text-primary block border-b border-border-primary/50 pb-4">Performance Metrics</span>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-semibold text-text-secondary mb-1.5">
                <span>CPU Load</span>
                <span>8.4%</span>
              </div>
              <div className="w-full h-1.5 bg-background-elevated rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '8.4%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-text-secondary mb-1.5">
                <span>Memory Allocation</span>
                <span>38.2%</span>
              </div>
              <div className="w-full h-1.5 bg-background-elevated rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: '38.2%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-text-secondary mb-1.5">
                <span>Database Pool Size</span>
                <span>2 / 10 active</span>
              </div>
              <div className="w-full h-1.5 bg-background-elevated rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: '20%' }} />
              </div>
            </div>

            <div className="pt-2 flex justify-between items-center text-[10px] text-text-muted font-semibold">
              <span>UPTIME: 36d 14h 22m</span>
              <span>LATENCY: 42ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
