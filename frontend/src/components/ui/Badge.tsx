import { ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { AlertCircle, CheckCircle2, Clock, Info, AlertTriangle } from 'lucide-react';

export type BadgeVariant = 
  | 'critical' 
  | 'high' 
  | 'medium' 
  | 'low' 
  | 'healthy' 
  | 'warning' 
  | 'exceeded' 
  | 'pending'
  | 'info';

interface BadgeProps {
  children: ReactNode;
  variant: BadgeVariant;
  className?: string;
  showIcon?: boolean;
}

export default function Badge({ 
  children, 
  variant, 
  className,
  showIcon = true 
}: BadgeProps) {
  
  const getIcon = () => {
    if (!showIcon) return null;
    
    switch (variant) {
      case 'critical':
      case 'exceeded':
        return <AlertCircle size={12} />;
      case 'high':
      case 'warning':
      case 'medium':
        return <AlertTriangle size={12} />;
      case 'healthy':
        return <CheckCircle2 size={12} />;
      case 'pending':
        return <Clock size={12} />;
      case 'low':
      case 'info':
        return <Info size={12} />;
      default:
        return null;
    }
  };

  const variantClasses: Record<BadgeVariant, string> = {
    critical: 'bg-danger/10 text-danger border border-danger/20',
    high: 'bg-warning/10 text-warning border border-warning/20',
    medium: 'bg-warning/10 text-warning border border-warning/20',
    warning: 'bg-warning/10 text-warning border border-warning/20',
    low: 'bg-accent-primary/10 text-accent-primary border border-accent-primary/20',
    info: 'bg-accent-primary/10 text-accent-primary border border-accent-primary/20',
    healthy: 'bg-success/10 text-success border border-success/20',
    exceeded: 'bg-danger/10 text-danger border border-danger/20',
    pending: 'bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20',
  };

  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide', variantClasses[variant], className)}>
      {getIcon()}
      {children}
    </span>
  );
}
