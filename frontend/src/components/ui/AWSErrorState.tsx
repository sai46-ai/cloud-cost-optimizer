import { AlertCircle, RefreshCw } from 'lucide-react';
import { Card, CardContent } from './Card';
import { Button } from './Button';

interface AWSErrorStateProps {
  onRetry: () => void;
  isLoading?: boolean;
}

export default function AWSErrorState({ onRetry, isLoading = false }: AWSErrorStateProps) {
  return (
    <Card className="animate-fade-in max-w-lg mx-auto my-12 border-red-500/20 bg-background-elevated/40 backdrop-blur-md overflow-hidden relative shadow-lg shadow-red-500/5">
      <div className="absolute top-0 right-0 w-64 h-64 bg-red-500/5 rounded-full blur-3xl pointer-events-none -mr-32 -mt-32"></div>
      <CardContent className="p-8 flex flex-col items-center text-center relative z-10">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 text-red-500 flex items-center justify-center mb-6 ring-1 ring-red-500/20">
          <AlertCircle size={32} />
        </div>
        
        <h3 className="text-xl font-bold text-text-primary tracking-tight mb-4">
          Unable to retrieve AWS data.
        </h3>
        
        <div className="text-left w-full max-w-xs mb-8 p-4 rounded-lg bg-background-secondary/20 border border-border-primary">
          <p className="text-xs font-semibold text-text-secondary mb-2">Possible reasons:</p>
          <ul className="text-xs text-text-muted space-y-1.5 list-disc pl-4">
            <li>Expired credentials</li>
            <li>Missing IAM permissions</li>
            <li>AWS service unavailable</li>
            <li>Network issue</li>
          </ul>
        </div>

        <Button 
          onClick={onRetry} 
          disabled={isLoading}
          className="px-6 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 hover:border-red-500/30 flex items-center gap-2 font-medium text-xs rounded-lg transition-all"
        >
          <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
          {isLoading ? "Retrying..." : "Retry"}
        </Button>
      </CardContent>
    </Card>
  );
}
