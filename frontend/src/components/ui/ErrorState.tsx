import { AlertTriangle } from 'lucide-react';
import { Card, CardContent } from './Card';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ title = 'Error Loading Data', message, onRetry }: ErrorStateProps) {
  return (
    <Card className="animate-fade-in max-w-lg mx-auto my-8 border-danger/20">
      <CardContent className="p-8 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-full bg-danger/10 text-danger flex items-center justify-center mb-4">
          <AlertTriangle size={32} />
        </div>
        <h3 className="text-xl font-bold text-text-primary mb-2">{title}</h3>
        <p className="text-text-secondary mb-6">{message}</p>
        {onRetry && (
          <Button onClick={onRetry}>
            Try Again
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
