import { useEffect, useState, useCallback } from 'react';
import { recommendationService } from '../services/api';
import { formatCurrency } from '../lib/utils';
import { Check, X, Server, Database, HardDrive, Cpu, AlertTriangle } from 'lucide-react';
import Badge from '../components/ui/Badge';
import PageTransition from '../components/layout/PageTransition';
import { motion } from 'framer-motion';
import { Skeleton, SkeletonTable } from '../components/ui/Skeleton';
import EmptyState from '../components/ui/EmptyState';
import useStore from '../store';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import AWSOnboardingState from '../components/ui/AWSOnboardingState';
import AWSErrorState from '../components/ui/AWSErrorState';

export default function Resources() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasAWSError, setHasAWSError] = useState(false);
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('savings-desc');
  const { user } = useStore();

  const loadData = useCallback(async () => {
    if (user && !user.is_demo_mode && !user.is_aws_connected) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setHasAWSError(false);
    try {
      const data = await recommendationService.getRecommendations();
      const list = Array.isArray(data) ? data : [];
      // Filter out non-pending recommendations
      setRecommendations(list.filter((r: any) => r.status === 'pending'));
    } catch (err: any) {
      console.error("Failed to load recommendations:", err);
      setRecommendations([]);
      if (err.message && (err.message.includes("AWS_ERROR") || err.message.includes("AWS") || err.message.includes("credentials") || err.message.includes("502"))) {
        setHasAWSError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAction = async (id: string, action: 'implement' | 'dismiss') => {
    try {
      const status = action === 'implement' ? 'implemented' : 'dismissed';
      await recommendationService.updateStatus(id, status);
      // Optimistic update
      setRecommendations(recs => recs.filter(r => r.id !== id));
    } catch (error) {
      console.error("Failed to update status:", error);
    }
  };

  const getResourceIcon = (type: string = '') => {
    switch ((type || '').toLowerCase()) {
      case 'ec2 instance': return <Server size={20} className="text-orange-500" />;
      case 'rds instance': return <Database size={20} className="text-accent-cyan" />;
      case 's3 bucket': return <HardDrive size={20} className="text-accent-primary" />;
      case 'ebs volume': return <HardDrive size={20} className="text-accent-primary" />;
      case 'lambda function': return <Cpu size={20} className="text-warning" />;
      default: return <Server size={20} className="text-text-muted" />;
    }
  };

  const totalSavings = recommendations.reduce((acc, curr) => acc + (curr.monthly_savings || 0), 0);

  const filteredRecs = recommendations
    .filter(rec => priorityFilter === 'all' || (rec.priority || '').toLowerCase() === priorityFilter.toLowerCase())
    .filter(rec => typeFilter === 'all' || (rec.resource_type || '').toLowerCase() === typeFilter.toLowerCase())
    .sort((a, b) => {
      if (sortBy === 'savings-desc') return (b.monthly_savings || 0) - (a.monthly_savings || 0);
      if (sortBy === 'savings-asc') return (a.monthly_savings || 0) - (b.monthly_savings || 0);
      if (sortBy === 'cost-desc') return (b.current_cost || 0) - (a.current_cost || 0);
      return 0;
    });

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 }
  };

  if (user && !user.is_demo_mode && !user.is_aws_connected) {
    return <AWSOnboardingState />;
  }

  if (hasAWSError) {
    return <AWSErrorState onRetry={loadData} isLoading={loading} />;
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-end mb-8">
          <div className="space-y-2">
            <Skeleton className="h-8 w-[250px]" />
            <Skeleton className="h-4 w-[350px]" />
          </div>
          <Skeleton className="h-10 w-[220px] rounded-lg" />
        </div>
        <Card className="space-y-6">
          <CardHeader className="pb-4 border-b border-border-primary">
            <Skeleton className="h-6 w-[200px]" />
          </CardHeader>
          <CardContent className="space-y-6 divide-y divide-border-primary pt-0">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="py-6 flex flex-col md:flex-row gap-6 md:items-center justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <Skeleton className="w-10 h-10 rounded-lg shrink-0" />
                  <div className="space-y-2 flex-1">
                    <div className="flex gap-2">
                      <Skeleton className="h-5 w-[150px]" />
                      <Skeleton className="h-5 w-[80px]" />
                      <Skeleton className="h-5 w-[60px]" />
                    </div>
                    <Skeleton className="h-4 w-[80%]" />
                    <Skeleton className="h-3 w-[120px]" />
                  </div>
                </div>
                <div className="flex md:flex-col items-center justify-end gap-3 shrink-0 md:pl-6">
                  <Skeleton className="h-6 w-[80px]" />
                  <div className="flex gap-2">
                    <Skeleton className="h-8 w-[70px] rounded-lg" />
                    <Skeleton className="h-8 w-[70px] rounded-lg" />
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <PageTransition>
      <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-2">Resource Optimizer</h2>
          <p className="text-text-secondary text-sm">AI-identified opportunities to right-size or terminate resources.</p>
        </div>
        <div className="bg-success/10 text-success px-4 py-2 rounded-lg border border-success/20 font-medium flex items-center gap-2 text-sm shadow-sm">
          <AlertTriangle size={18} />
          Potential Savings: {formatCurrency(totalSavings)}/mo
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-border-primary pb-4">
          <CardTitle>Actionable Recommendations ({filteredRecs.length})</CardTitle>
        </CardHeader>

        {/* Filters Controls */}
        <div className="flex flex-col sm:flex-row gap-4 p-4 border-b border-border-primary bg-background-elevated/30">
          <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Priority</label>
              <select 
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border-primary bg-background-primary text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary/30 focus:border-accent-primary"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Resource Type</label>
              <select 
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border-primary bg-background-primary text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary/30 focus:border-accent-primary"
              >
                <option value="all">All Types</option>
                <option value="ec2 instance">EC2 Instance</option>
                <option value="rds instance">RDS Instance</option>
                <option value="s3 bucket">S3 Bucket</option>
                <option value="ebs volume">EBS Volume</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Sort By</label>
              <select 
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border-primary bg-background-primary text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary/30 focus:border-accent-primary"
              >
                <option value="savings-desc">Savings: High to Low</option>
                <option value="savings-asc">Savings: Low to High</option>
                <option value="cost-desc">Current Cost: High to Low</option>
              </select>
            </div>
          </div>
        </div>
        
        <CardContent className="p-0">
          {filteredRecs.length > 0 ? (
            <motion.div variants={containerVariants} initial="hidden" animate="show" className="divide-y divide-border-primary">
              {filteredRecs.map((rec) => (
                <motion.div variants={itemVariants} key={rec.id} className="p-6 flex flex-col md:flex-row gap-6 md:items-center hover:bg-background-elevated transition-colors">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-background-elevated border border-border-primary flex items-center justify-center shrink-0">
                      {getResourceIcon(rec.resource_type)}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <h4 className="font-semibold text-text-primary">{rec.resource_id}</h4>
                        <Badge variant={rec.priority === 'high' ? 'critical' : rec.priority === 'medium' ? 'warning' : 'low'}>
                          {rec.priority.charAt(0).toUpperCase() + rec.priority.slice(1)} Priority
                        </Badge>
                        <Badge variant="info">{rec.category}</Badge>
                      </div>
                      <p className="text-sm text-text-secondary mb-2">{rec.recommendation}</p>
                      <div className="flex items-center gap-4 text-xs font-medium">
                        <span className="text-text-muted line-through">{formatCurrency(rec.current_cost)}/mo</span>
                        <span className="text-success">→ {formatCurrency(rec.optimized_cost)}/mo</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex md:flex-col items-center justify-between md:justify-end gap-4 shrink-0 md:pl-6 border-t md:border-t-0 md:border-l border-border-primary pt-4 md:pt-0">
                    <div className="text-left md:text-center">
                      <div className="text-xs text-text-secondary mb-1 uppercase tracking-wider font-semibold">Savings</div>
                      <div className="text-lg font-bold text-success">+{formatCurrency(rec.monthly_savings)}</div>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        variant="secondary"
                        size="sm"
                        onClick={() => handleAction(rec.id, 'dismiss')}
                      >
                        <X size={14} className="mr-1" /> Dismiss
                      </Button>
                      <Button 
                        size="sm"
                        className="bg-success text-[#FAFAFA] hover:bg-green-600 focus:ring-success/20"
                        onClick={() => handleAction(rec.id, 'implement')}
                      >
                        <Check size={14} className="mr-1" /> Apply
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <div className="p-6">
              <EmptyState
                icon={<Check size={48} className="text-success" />}
                title={recommendations.length > 0 ? "No Match Found" : "Infrastructure is Highly Optimized"}
                description={recommendations.length > 0 ? "No recommendations match your current filtering criteria." : "We couldn't find any actionable cost recommendations at this time. Great job keeping your resources efficient!"}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </PageTransition>
  );
}
