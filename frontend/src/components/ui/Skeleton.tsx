import { cn } from '../../lib/utils';
import { Card, CardContent } from './Card';

export type SkeletonProps = React.HTMLAttributes<HTMLDivElement>;

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-[var(--border-primary)] opacity-50", className)}
      {...props}
    />
  );
}

export function SkeletonCard() {
  return (
    <Card className="h-full flex flex-col">
      <CardContent className="p-6 flex flex-col h-full">
        <div className="flex items-center gap-3 mb-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[150px]" />
            <Skeleton className="h-3 w-[100px]" />
          </div>
        </div>
        <div className="space-y-3 mt-auto">
          <Skeleton className="h-8 w-[120px]" />
          <Skeleton className="h-3 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}



export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="w-full space-y-4">
      <div className="flex items-center gap-4 py-2">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-6 flex-grow" />
        ))}
      </div>
      <div className="border border-[var(--border-primary)] rounded-lg divide-y divide-[var(--border-primary)] bg-[var(--bg-secondary)]">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-4 flex gap-4">
            {Array.from({ length: cols }).map((_, j) => (
              <Skeleton key={j} className={cn("h-4 flex-grow", j === 0 ? "max-w-[120px]" : "max-w-[200px]")} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonChat() {
  return (
    <div className="space-y-6 p-4">
      <div className="flex items-start gap-3">
        <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
        <div className="space-y-2 max-w-[70%]">
          <Skeleton className="h-4 w-[120px]" />
          <Skeleton className="h-12 w-[280px] rounded-tl-none" />
        </div>
      </div>
      <div className="flex items-start gap-3 justify-end">
        <div className="space-y-2 max-w-[70%] flex flex-col items-end">
          <Skeleton className="h-4 w-[100px]" />
          <Skeleton className="h-10 w-[200px] rounded-tr-none" />
        </div>
        <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
      </div>
      <div className="flex items-start gap-3">
        <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
        <div className="space-y-2 max-w-[70%]">
          <Skeleton className="h-4 w-[150px]" />
          <Skeleton className="h-16 w-[320px] rounded-tl-none" />
        </div>
      </div>
    </div>
  );
}
