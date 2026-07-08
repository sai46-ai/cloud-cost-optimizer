import { ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn, formatCurrency, formatNumber } from '../../lib/utils';
import { Card } from './Card';

interface MetricCardProps {
  title: string;
  value: number;
  type?: 'currency' | 'number' | 'percentage';
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
  iconColor?: 'purple' | 'green' | 'blue' | 'amber' | 'red';
  className?: string;
  sparklineData?: number[];
}

export default function MetricCard({
  title,
  value,
  type = 'currency',
  change,
  trend,
  icon,
  iconColor = 'purple',
  className,
  sparklineData,
}: MetricCardProps) {
  
  const formattedValue = type === 'currency' 
    ? formatCurrency(value)
    : type === 'percentage'
      ? `${formatNumber(value)}%`
      : formatNumber(value);

  // Auto-determine trend if not explicitly provided
  const actualTrend = trend || (change ? (change > 0 ? 'up' : change < 0 ? 'down' : 'neutral') : 'neutral');
  
  // For cost, 'down' is usually good (green) and 'up' is bad (red)
  const isPositive = actualTrend === 'down'; 

  const renderSparkline = (data: number[], colorClass: string) => {
    if (!data || data.length === 0) return null;
    const width = 100;
    const height = 25;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const points = data.map((val, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    const strokeColor = colorClass === 'green' ? 'var(--success)' : colorClass === 'red' ? 'var(--danger)' : colorClass === 'blue' ? 'var(--accent-cyan)' : 'var(--accent-primary)';

    return (
      <svg width={width} height={height} className="overflow-visible opacity-70 transition-all duration-300">
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      </svg>
    );
  };

  return (
    <Card className={cn('p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 relative overflow-hidden group', className)}>
      <div className="flex justify-between items-start mb-4">
        <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-4', {
          'bg-accent-primary/10 text-accent-primary': iconColor === 'purple',
          'bg-success/10 text-success': iconColor === 'green',
          'bg-accent-cyan/10 text-accent-cyan': iconColor === 'blue',
          'bg-warning/10 text-warning': iconColor === 'amber',
          'bg-danger/10 text-danger': iconColor === 'red'
        })}>
          {icon}
        </div>
        
        {change !== undefined && (
          <div className={cn(
            'inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full', 
            isPositive ? 'text-success bg-success/10' : actualTrend === 'up' ? 'text-danger bg-danger/10' : 'bg-background-elevated text-text-muted'
          )}>
            {actualTrend === 'up' ? <TrendingUp size={14} /> : actualTrend === 'down' ? <TrendingDown size={14} /> : <Minus size={14} />}
            <span>{Math.abs(change).toFixed(1)}%</span>
          </div>
        )}
      </div>
      
      <div className="flex justify-between items-end">
        <div>
          <h3 className="text-sm font-medium text-text-secondary mb-1">{title}</h3>
          <div className="text-3xl font-bold tracking-tight text-text-primary mb-2">{formattedValue}</div>
        </div>
        {sparklineData && renderSparkline(sparklineData, iconColor)}
      </div>
    </Card>
  );
}
