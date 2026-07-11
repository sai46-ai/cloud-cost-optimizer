import { useEffect, useState, useCallback } from 'react';
import { costService, reportService, BACKEND_URL } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatCurrency } from '../lib/utils';
import useStore from '../store';
import Badge from '../components/ui/Badge';
import PageTransition from '../components/layout/PageTransition';
import { motion, AnimatePresence } from 'framer-motion';
import { Filter, Download, X } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { AnalyticsNetworkGraph } from '../components/3d/Internal3DElements';
import AWSOnboardingState from '../components/ui/AWSOnboardingState';
import AWSErrorState from '../components/ui/AWSErrorState';

export default function CostAnalytics() {
  const [costs, setCosts] = useState<any[]>([]);
  const [breakdown, setBreakdown] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [hasAWSError, setHasAWSError] = useState(false);
  
  // Default dates
  const defaultStartDate = () => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  };
  const defaultEndDate = () => new Date().toISOString().split('T')[0];

  // Filter states
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [endDate, setEndDate] = useState(defaultEndDate);
  const [selectedService, setSelectedService] = useState('All Services');
  const [isExporting, setIsExporting] = useState(false);

  const isFiltered = selectedService !== 'All Services' || 
    startDate !== defaultStartDate() || 
    endDate !== defaultEndDate();

  const { theme, addToast, user } = useStore();

  const loadData = useCallback(async (startStr?: string, endStr?: string, serviceStr?: string) => {
    if (user && !user.is_demo_mode && !user.is_aws_connected) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setHasAWSError(false);
    try {
      const activeSvc = serviceStr === 'All Services' ? undefined : serviceStr;
      const [costData, breakdownData] = await Promise.all([
        costService.getCosts(startStr, endStr, activeSvc),
        costService.getBreakdown(startStr, endStr)
      ]);
      setCosts(costData);
      setBreakdown(breakdownData);
    } catch (error: any) {
      console.error("Failed to load cost analytics:", error);
      if (error.message && (error.message.includes("AWS_ERROR") || error.message.includes("AWS") || error.message.includes("credentials") || error.message.includes("502"))) {
        setHasAWSError(true);
      } else {
        addToast("Failed to load cost data", "error");
      }
    } finally {
      setLoading(false);
    }
  }, [addToast, user]);

  useEffect(() => {
    loadData(startDate, endDate, selectedService);
  }, [loadData, startDate, endDate, selectedService, user?.is_aws_connected, user?.is_demo_mode]);

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setShowFilterModal(false);
    loadData(startDate, endDate, selectedService);
    addToast("Filters applied successfully", "success");
  };

  const handleExportCSV = async () => {
    setIsExporting(true);
    addToast("Generating CSV Export...", "info");
    try {
      const report = await reportService.generateReport({
        report_type: 'detailed_breakdown',
        format: 'csv'
      });
      // Redirect to the static URL download
      const downloadUrl = `${BACKEND_URL}/static/reports/${report.filename}`;
      window.open(downloadUrl, '_blank');
      addToast("CSV Export downloaded successfully", "success");
    } catch (err: any) {
      addToast(err.message || "Failed to generate CSV export", "error");
    } finally {
      setIsExporting(false);
    }
  };

  if (user && !user.is_demo_mode && !user.is_aws_connected) {
    return <AWSOnboardingState />;
  }

  if (hasAWSError) {
    return <AWSErrorState onRetry={() => loadData(startDate, endDate, selectedService)} isLoading={loading} />;
  }

  if (loading && costs.length === 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex justify-between items-end mb-8">
          <div className="space-y-2">
            <Skeleton className="h-8 w-[200px]" />
            <Skeleton className="h-4 w-[300px]" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-10 w-[120px] rounded-lg" />
            <Skeleton className="h-10 w-[100px] rounded-lg" />
          </div>
        </div>
        <Card>
          <CardHeader className="border-b border-border-primary pb-4">
            <Skeleton className="h-6 w-[300px]" />
          </CardHeader>
          <CardContent className="pt-6">
            <Skeleton className="h-[350px] w-full rounded-xl" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Process data for the stacked bar chart (top 5 services over time)
  const topServices = breakdown?.by_service.slice(0, 5).map((s: any) => s.service) || [];
  
  // Create a daily map
  const dailyDataMap = new Map();
  costs.forEach(record => {
    const date = new Date(record.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (!dailyDataMap.has(date)) {
      dailyDataMap.set(date, { date });
    }
    const dayData = dailyDataMap.get(date);
    if (topServices.includes(record.service)) {
      dayData[record.service] = (dayData[record.service] || 0) + record.amount;
    } else {
      dayData['Other'] = (dayData['Other'] || 0) + record.amount;
    }
  });

  const chartData = Array.from(dailyDataMap.values()).slice(-14); // Last 14 days
  const colors = ['#6366f1', '#8b5cf6', '#06b6d4', '#22c55e', '#f59e0b', '#6b7280'];

  const tableContainerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const tableRowVariants = {
    hidden: { opacity: 0, x: -10 },
    show: { opacity: 1, x: 0 }
  };

  return (
    <PageTransition>
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8 relative">
        <div className="relative z-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Cost Analytics</h2>
          <p className="text-text-secondary font-medium">Deep dive into your AWS spending patterns.</p>
        </div>
        <AnalyticsNetworkGraph />
        <div className="flex gap-2">
          {isFiltered && (
            <Button 
              variant="secondary"
              className="flex items-center gap-1.5 text-xs text-danger border-danger/20 hover:bg-danger/10 hover:border-danger/30" 
              onClick={() => {
                const start = defaultStartDate();
                const end = defaultEndDate();
                setStartDate(start);
                setEndDate(end);
                setSelectedService('All Services');
                loadData(start, end, 'All Services');
                addToast("Filters cleared", "info");
              }}
            >
              <X size={14} /> Clear Filters
            </Button>
          )}
          <Button variant="secondary" className="flex items-center gap-2" onClick={handleExportCSV} disabled={isExporting}>
            <Download size={16} />
            {isExporting ? "Exporting..." : "Export CSV"}
          </Button>
          <Button className="flex items-center gap-2" onClick={() => setShowFilterModal(true)}>
            <Filter size={16} />
            Filter
          </Button>
        </div>
      </div>

      <div className={`transition-opacity duration-200 ${loading ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
        <Card className="mb-8">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold text-text-primary">Daily Spending by Service (Last 14 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[380px] w-full min-h-[380px]">
              <ResponsiveContainer width="100%" height={380} minWidth={0}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.05)'} />
                  <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 500 }} />
                  <YAxis tickLine={false} axisLine={false} tickFormatter={(value) => `$${value}`} tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 500 }} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'var(--bg-elevated)', borderColor: 'var(--border-primary)', borderRadius: '12px', boxShadow: 'var(--shadow-premium)' }}
                    labelStyle={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: '600', marginBottom: '4px' }}
                    itemStyle={{ fontSize: '11px', fontWeight: '500' }}
                    cursor={{ fill: theme === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(15,23,42,0.03)' }}
                    formatter={(value: any) => [formatCurrency(value as number)]}
                  />
                  <Legend />
                  {topServices.map((service: string, index: number) => (
                    <Bar key={service} dataKey={service} stackId="a" fill={colors[index % colors.length]} />
                  ))}
                  <Bar dataKey="Other" stackId="a" fill={colors[colors.length - 1]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card className="overflow-hidden">
            <CardHeader className="pb-3 bg-background-elevated/40 border-b border-border-primary/60">
              <CardTitle className="text-base font-bold text-text-primary">Service Breakdown</CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-text-secondary">
                <thead className="text-[10px] uppercase font-bold tracking-wider bg-background-elevated text-text-muted border-b border-border-primary">
                  <tr>
                    <th className="px-5 py-3">Service</th>
                    <th className="px-5 py-3">Total Cost</th>
                    <th className="px-5 py-3">% of Total</th>
                  </tr>
                </thead>
                <motion.tbody variants={tableContainerVariants} initial="hidden" animate="show" key={costs.length} className="divide-y divide-border-primary/50 bg-background-secondary/20">
                  {breakdown?.by_service.map((item: any, idx: number) => (
                    <motion.tr variants={tableRowVariants} key={item.service} className="hover:bg-background-elevated/60 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5 text-text-primary font-medium">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colors[idx % colors.length] }}></div>
                          {item.service}
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-bold text-text-primary">{formatCurrency(item.amount)}</td>
                      <td className="px-5 py-3.5 font-medium">{item.percentage.toFixed(1)}%</td>
                    </motion.tr>
                  ))}
                </motion.tbody>
              </table>
            </div>
          </Card>

          <Card className="overflow-hidden">
            <CardHeader className="pb-3 bg-background-elevated/40 border-b border-border-primary/60">
              <CardTitle className="text-base font-bold text-text-primary">Region Breakdown</CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-text-secondary">
                <thead className="text-[10px] uppercase font-bold tracking-wider bg-background-elevated text-text-muted border-b border-border-primary">
                  <tr>
                    <th className="px-5 py-3">Region</th>
                    <th className="px-5 py-3">Total Cost</th>
                    <th className="px-5 py-3">% of Total</th>
                  </tr>
                </thead>
                <motion.tbody variants={tableContainerVariants} initial="hidden" animate="show" key={costs.length + 1} className="divide-y divide-border-primary/50 bg-background-secondary/20">
                  {breakdown?.by_region.map((item: any) => (
                    <motion.tr variants={tableRowVariants} key={item.region} className="hover:bg-background-elevated/60 transition-colors">
                      <td className="px-5 py-3.5 font-medium"><Badge variant="info" showIcon={false}>{item.region}</Badge></td>
                      <td className="px-5 py-3.5 font-bold text-text-primary">{formatCurrency(item.amount)}</td>
                      <td className="px-5 py-3.5 font-medium">{item.percentage.toFixed(1)}%</td>
                    </motion.tr>
                  ))}
                </motion.tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>

      {/* Filter Modal Dialog */}
      <AnimatePresence>
        {showFilterModal && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={() => setShowFilterModal(false)}
          >
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md bg-background-card border border-border-primary rounded-xl relative shadow-2xl p-6"
            >
              <button className="absolute top-4 right-4 text-text-muted hover:text-text-primary" onClick={() => setShowFilterModal(false)}>
                <X size={18} />
              </button>
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Filter size={20} className="text-accent-primary" /> Filter Cost Records
              </h3>
              <form onSubmit={handleApplyFilters} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Service Filter</label>
                  <select 
                    className="flex h-10 w-full rounded-lg border border-border-primary bg-background-primary px-3 py-2 text-sm text-text-primary focus-visible:outline-none focus-visible:border-accent-primary focus-visible:ring-2 focus-visible:ring-accent-primary/20 disabled:cursor-not-allowed disabled:opacity-55 transition-all duration-200 shadow-sm" 
                    value={selectedService} 
                    onChange={(e) => setSelectedService(e.target.value)}
                  >
                    <option value="All Services">All Services</option>
                    <option value="Amazon EC2">Amazon EC2</option>
                    <option value="Amazon RDS">Amazon RDS</option>
                    <option value="Amazon S3">Amazon S3</option>
                    <option value="AWS Lambda">AWS Lambda</option>
                    <option value="Amazon CloudFront">Amazon CloudFront</option>
                    <option value="Amazon DynamoDB">Amazon DynamoDB</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Start Date</label>
                  <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">End Date</label>
                  <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
                </div>

                <div className="pt-4 border-t border-border-secondary flex justify-end gap-3 mt-4">
                  <Button type="button" variant="secondary" onClick={() => setShowFilterModal(false)}>Cancel</Button>
                  <Button type="submit">Apply Filters</Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </PageTransition>
  );
}
