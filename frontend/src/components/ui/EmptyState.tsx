import { ReactNode } from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-14 text-center border border-dashed border-border-primary rounded-2xl bg-background-secondary/40 animate-fade-in">
      {icon && (
        <div className="w-12 h-12 rounded-xl bg-background-elevated border border-border-primary/50 text-text-muted flex items-center justify-center mb-5 shadow-sm select-none">
          {icon}
        </div>
      )}
      <h3 className="text-base font-bold text-text-primary mb-1.5">{title}</h3>
      <p className="text-xs text-text-secondary max-w-xs mb-6 leading-relaxed">{description}</p>
      {action && (
        <Button onClick={action.onClick} size="sm">
          {action.label}
        </Button>
      )}
    </div>
  );
}
