/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background-primary disabled:pointer-events-none disabled:opacity-50 gap-2 cursor-pointer active:scale-[0.98] select-none',
  {
    variants: {
      variant: {
        default: 'bg-accent-primary text-[#FAFAFA] hover:bg-accent-primary-hover shadow-sm shadow-accent-primary/10 border border-accent-primary/20',
        secondary: 'bg-background-elevated text-text-primary border border-border-primary hover:bg-background-secondary hover:border-border-primary/80 shadow-sm',
        ghost: 'hover:bg-background-secondary/60 text-text-secondary hover:text-text-primary border border-transparent',
        danger: 'bg-danger/10 text-danger hover:bg-danger/20 border border-danger/20',
        glass: 'glass-panel text-[#FAFAFA] hover:bg-background-elevated/40 border-border-primary',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-11 rounded-lg px-8 text-base',
        icon: 'h-9 w-9 rounded-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
