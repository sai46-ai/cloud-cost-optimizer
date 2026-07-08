import { useEffect, useState } from 'react';
import { budgetService } from '../services/api';
import { formatCurrency } from '../lib/utils';
import { Bell, Plus, Edit2, Trash2, Wallet, X } from 'lucide-react';
import Badge from '../components/ui/Badge';
import { SkeletonCard } from '../components/ui/Skeleton';
import PageTransition from '../components/layout/PageTransition';
import { motion, AnimatePresence } from 'framer-motion';
import useStore from '../store';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export default function Budgets() {
  const [budgets, setBudgets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useStore();

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState<any>(null);

  // Form states
  const [name, setName] = useState('');
  const [amount, setAmount] = useState('');
  const [period, setPeriod] = useState('monthly');
  const [threshold50, setThreshold50] = useState(true);
  const [threshold80, setThreshold80] = useState(true);
  const [threshold90, setThreshold90] = useState(true);
  const [threshold100, setThreshold100] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadData() {
    try {
      const data = await budgetService.getBudgets();
      setBudgets(data);
    } catch (error) {
      console.error("Failed to load budgets:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const openCreateModal = () => {
    setName('');
    setAmount('');
    setPeriod('monthly');
    setThreshold50(true);
    setThreshold80(true);
    setThreshold90(true);
    setThreshold100(true);
    setShowCreateModal(true);
  };

  const openEditModal = (budget: any) => {
    setSelectedBudget(budget);
    setName(budget.name);
    setAmount(budget.amount.toString());
    setPeriod(budget.period);
    setThreshold50(budget.alert_threshold_50);
    setThreshold80(budget.alert_threshold_80);
    setThreshold90(budget.alert_threshold_90);
    setThreshold100(budget.alert_threshold_100);
    setShowEditModal(true);
  };

  const openDeleteModal = (budget: any) => {
    setSelectedBudget(budget);
    setShowDeleteModal(true);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !amount.trim() || parseFloat(amount) <= 0) {
      addToast('Please enter a valid budget name and positive amount', 'warning');
      return;
    }
    setIsSubmitting(true);
    try {
      const payload = {
        name,
        amount: parseFloat(amount),
        period,
        alert_threshold_50: threshold50,
        alert_threshold_80: threshold80,
        alert_threshold_90: threshold90,
        alert_threshold_100: threshold100,
        email_enabled: true,
        sns_enabled: false,
        dashboard_enabled: true
      };
      await budgetService.createBudget(payload);
      addToast('Budget created successfully', 'success');
      setShowCreateModal(false);
      loadData();
    } catch (err: any) {
      addToast(err.message || 'Failed to create budget', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !amount.trim() || parseFloat(amount) <= 0) {
      addToast('Please enter a valid budget name and positive amount', 'warning');
      return;
    }
    setIsSubmitting(true);
    try {
      const payload = {
        name,
        amount: parseFloat(amount),
        period,
        alert_threshold_50: threshold50,
        alert_threshold_80: threshold80,
        alert_threshold_90: threshold90,
        alert_threshold_100: threshold100
      };
      await budgetService.updateBudget(selectedBudget.id, payload);
      addToast('Budget updated successfully', 'success');
      setShowEditModal(false);
      loadData();
    } catch (err: any) {
      addToast(err.message || 'Failed to update budget', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setIsSubmitting(true);
    try {
      await budgetService.deleteBudget(selectedBudget.id);
      addToast('Budget deleted successfully', 'success');
      setShowDeleteModal(false);
      loadData();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete budget', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (budget: any) => {
    if (budget.spent > budget.amount) {
      return <Badge variant="exceeded">Exceeded</Badge>;
    }
    if (budget.spent > budget.amount * 0.9) {
      return <Badge variant="critical">Critical (90%+)</Badge>;
    }
    if (budget.spent > budget.amount * 0.8) {
      return <Badge variant="warning">Warning (80%+)</Badge>;
    }
    return <Badge variant="healthy">On Track</Badge>;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  return (
    <PageTransition>
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-2">Budgets & Alerts</h2>
          <p className="text-text-secondary text-sm">Set limits and receive notifications before costs spiral.</p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus size={18} className="mr-2" />
          Create Budget
        </Button>
      </div>

      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {budgets.map(budget => {
          const percentUsed = Math.min(budget.utilization_pct || 0, 100);
          const isExceeded = percentUsed >= 100;
          const isWarning = percentUsed >= 80 && !isExceeded;

          const thresholds = [];
          if (budget.alert_threshold_50) thresholds.push(50);
          if (budget.alert_threshold_80) thresholds.push(80);
          if (budget.alert_threshold_90) thresholds.push(90);
          if (budget.alert_threshold_100) thresholds.push(100);

          return (
            <motion.div variants={itemVariants} key={budget.id}>
              <Card className="relative overflow-hidden group h-full flex flex-col">
                <CardHeader className="border-b border-border-primary pb-4 mb-4 flex flex-row justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-text-primary">{budget.name}</h3>
                    <div className="text-xs text-text-secondary mt-1">
                      {budget.service ? budget.service : 'All Services'} • {budget.period}
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-background-elevated h-8 w-8 text-text-secondary" onClick={() => openEditModal(budget)}><Edit2 size={14} /></button>
                    <button className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-danger/10 h-8 w-8 text-danger" onClick={() => openDeleteModal(budget)}><Trash2 size={14} /></button>
                  </div>
                </CardHeader>

                <CardContent className="flex-1 flex flex-col">
                  <div className="mb-6 flex-1">
                    <div className="flex justify-between items-end mb-2">
                      <div className="text-2xl font-bold">{formatCurrency(budget.spent)}</div>
                      <div className="text-sm text-text-secondary">of {formatCurrency(budget.amount)}</div>
                    </div>
                    
                    <div className="h-2 w-full bg-border-primary rounded-full overflow-hidden mb-2">
                      <div 
                        className={`h-full transition-all duration-500 ease-out ${isExceeded ? 'bg-danger' : isWarning ? 'bg-warning' : 'bg-success'}`}
                        style={{ width: `${percentUsed}%` }}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-text-secondary">{(budget.utilization_pct || 0).toFixed(1)}% Used</span>
                      {getStatusBadge(budget)}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-4 border-t border-border-primary mt-auto">
                    {thresholds.map((t: number) => (
                      <div key={t} className="flex items-center gap-1 text-xs bg-background-elevated px-2 py-1 rounded border border-border-primary">
                        <Bell size={12} className={budget.spent >= budget.amount * (t/100) ? "text-danger" : "text-text-muted"} />
                        <span className={budget.spent >= budget.amount * (t/100) ? "text-danger font-medium" : "text-text-secondary"}>
                          {t}% Alert
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {budgets.length === 0 && (
          <div className="col-span-full border border-dashed border-border-primary rounded-xl p-12 flex flex-col items-center justify-center bg-background-secondary/50">
            <Wallet size={48} className="text-text-muted mb-4" />
            <h3 className="text-lg font-medium mb-2 text-text-primary">No Budgets Found</h3>
            <p className="max-w-md text-center mb-6 text-text-secondary">Create a budget to track spending for specific services or your entire account.</p>
            <Button onClick={openCreateModal}><Plus size={18} className="mr-2" /> Create First Budget</Button>
          </div>
        )}
      </motion.div>

      {/* Modal Dialog Overlay container */}
      <AnimatePresence>
        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#111827]/70 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-lg bg-background-card border border-border-primary rounded-xl relative shadow-2xl p-6"
            >
              <button className="absolute top-4 right-4 text-text-muted hover:text-text-primary" onClick={() => setShowCreateModal(false)}>
                <X size={18} />
              </button>
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Wallet size={20} className="text-accent-primary" /> Create New Budget
              </h3>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Budget Name</label>
                  <Input type="text" placeholder="e.g. AWS Production Limit" value={name} onChange={(e) => setName(e.target.value)} required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Limit Amount ($)</label>
                    <Input type="number" placeholder="e.g. 5000" value={amount} onChange={(e) => setAmount(e.target.value)} required min="1" step="any" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Period</label>
                    <select 
                      className="w-full h-10 px-3 py-2 rounded-md border border-border-primary bg-background-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent transition-colors text-text-primary" 
                      value={period} 
                      onChange={(e) => setPeriod(e.target.value)}
                    >
                      <option value="monthly">Monthly</option>
                      <option value="weekly">Weekly</option>
                      <option value="daily">Daily</option>
                    </select>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Notification Thresholds</label>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold50} onChange={(e) => setThreshold50(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 50% Limit Alert
                    </label>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold80} onChange={(e) => setThreshold80(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 80% Limit Alert
                    </label>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold90} onChange={(e) => setThreshold90(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 90% Limit Alert
                    </label>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold100} onChange={(e) => setThreshold100(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 100% Limit Alert
                    </label>
                  </div>
                </div>

                <div className="pt-4 border-t border-border-primary flex justify-end gap-3 mt-6">
                  <Button type="button" variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                  <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Submitting..." : "Create"}</Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#111827]/70 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-lg bg-background-card border border-border-primary rounded-xl relative shadow-2xl p-6"
            >
              <button className="absolute top-4 right-4 text-text-muted hover:text-text-primary" onClick={() => setShowEditModal(false)}>
                <X size={18} />
              </button>
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Wallet size={20} className="text-accent-primary" /> Edit Budget
              </h3>
              <form onSubmit={handleEdit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Budget Name</label>
                  <Input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Limit Amount ($)</label>
                    <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required min="1" step="any" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Period</label>
                    <select 
                      className="w-full h-10 px-3 py-2 rounded-md border border-border-primary bg-background-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent transition-colors text-text-primary" 
                      value={period} 
                      onChange={(e) => setPeriod(e.target.value)}
                    >
                      <option value="monthly">Monthly</option>
                      <option value="weekly">Weekly</option>
                      <option value="daily">Daily</option>
                    </select>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Notification Thresholds</label>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold50} onChange={(e) => setThreshold50(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 50% Limit Alert
                    </label>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold80} onChange={(e) => setThreshold80(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 80% Limit Alert
                    </label>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold90} onChange={(e) => setThreshold90(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 90% Limit Alert
                    </label>
                    <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                      <input type="checkbox" checked={threshold100} onChange={(e) => setThreshold100(e.target.checked)} className="rounded border-border-primary text-accent-primary focus:ring-accent-primary" /> 100% Limit Alert
                    </label>
                  </div>
                </div>

                <div className="pt-4 border-t border-border-primary flex justify-end gap-3 mt-6">
                  <Button type="button" variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
                  <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Updating..." : "Save Changes"}</Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#111827]/70 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md bg-background-card border border-border-primary p-6 rounded-xl shadow-2xl text-center"
            >
              <h3 className="text-lg font-bold text-danger mb-2 flex items-center justify-center gap-2">
                <Trash2 size={24} /> Delete Budget?
              </h3>
              <p className="text-sm text-text-secondary mb-6">
                Are you sure you want to delete the budget <strong>"{selectedBudget?.name}"</strong>? This action cannot be undone.
              </p>
              <div className="flex justify-center gap-3">
                <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
                <Button className="bg-danger hover:bg-danger/90 text-[#FAFAFA]" onClick={handleDelete} disabled={isSubmitting}>
                  {isSubmitting ? "Deleting..." : "Confirm Delete"}
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </PageTransition>
  );
}
