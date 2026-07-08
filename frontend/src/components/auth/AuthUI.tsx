import React from 'react';
import { cn } from '../../lib/utils';

// --- Auth Card ---
export const AuthCard = ({ children, className }: { children: React.ReactNode; className?: string }) => {
  return (
    <div className={cn(
      "w-full max-w-[440px] mx-auto p-8 sm:p-10 rounded-3xl bg-background-primary/80 backdrop-blur-2xl border border-border-subtle shadow-[0_8px_30px_rgb(0,0,0,0.12)]",
      className
    )}>
      {children}
    </div>
  );
};

// --- Auth Input ---
export type AuthInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  icon?: React.ReactNode;
};

export const AuthInput = React.forwardRef<HTMLInputElement, AuthInputProps>(
  ({ className, type, icon, ...props }, ref) => {
    return (
      <div className="relative group">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-text-muted group-focus-within:text-accent-primary transition-colors">
            {icon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            "flex h-12 w-full rounded-xl border border-border-primary bg-background-elevated px-4 py-2 text-[15px] text-text-primary transition-all duration-200 placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/30 focus-visible:border-accent-primary disabled:cursor-not-allowed disabled:opacity-50 hover:border-accent-primary/50",
            icon && "pl-12",
            className
          )}
          ref={ref}
          {...props}
        />
      </div>
    );
  }
);
AuthInput.displayName = "AuthInput";

// --- Auth Button ---
export interface AuthButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

export const AuthButton = React.forwardRef<HTMLButtonElement, AuthButtonProps>(
  ({ className, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={cn(
          "relative flex h-12 w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-accent-primary px-6 text-[15px] font-semibold text-white transition-all duration-300 hover:bg-accent-primary-hover hover:shadow-[0_0_20px_rgba(var(--accent-primary-rgb),0.3)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background-primary",
          className
        )}
        {...props}
      >
        {isLoading ? (
          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        ) : (
          children
        )}
      </button>
    );
  }
);
AuthButton.displayName = 'AuthButton';
