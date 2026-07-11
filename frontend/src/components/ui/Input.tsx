import React from 'react';
import { cn } from '../../lib/utils';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-lg border border-border-primary bg-background-primary px-3 py-2 text-sm text-text-primary file:border-0 file:bg-transparent file:text-xs file:font-medium placeholder:text-text-muted/65 focus-visible:outline-none focus-visible:border-accent-primary focus-visible:ring-2 focus-visible:ring-accent-primary/20 disabled:cursor-not-allowed disabled:opacity-55 transition-all duration-200 shadow-sm",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
