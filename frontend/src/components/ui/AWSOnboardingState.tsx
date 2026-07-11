import { Cloud, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from './Card';
import { Button } from './Button';

export default function AWSOnboardingState() {
  const navigate = useNavigate();

  return (
    <Card className="animate-fade-in max-w-2xl mx-auto my-12 border-accent-primary/20 bg-background-elevated/40 backdrop-blur-md overflow-hidden relative shadow-lg shadow-accent-primary/5">
      <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/5 rounded-full blur-3xl pointer-events-none -mr-32 -mt-32"></div>
      <CardContent className="p-10 flex flex-col items-center text-center relative z-10">
        <div className="w-20 h-20 rounded-2xl bg-accent-primary/10 text-accent-primary flex items-center justify-center mb-6 shadow-inner ring-1 ring-accent-primary/20 animate-pulse">
          <Cloud size={40} className="stroke-[1.5]" />
        </div>
        
        <h2 className="text-2xl font-bold text-text-primary tracking-tight mb-3">
          Connect your AWS account
        </h2>
        
        <p className="text-sm text-text-secondary max-w-lg mb-8 leading-relaxed">
          Connect your AWS account to monitor cloud costs, resources, budgets, and recommendations.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-md mb-8 text-left">
          <div className="p-4 rounded-lg bg-background-secondary/30 border border-border-primary">
            <div className="text-accent-primary mb-2">
              <ShieldCheck size={18} />
            </div>
            <h4 className="text-xs font-semibold text-text-primary mb-1">1. Secure Role</h4>
            <p className="text-[10px] text-text-muted leading-normal">Configure read-only IAM access for CloudWise.</p>
          </div>
          <div className="p-4 rounded-lg bg-background-secondary/30 border border-border-primary">
            <div className="text-accent-primary mb-2">
              <Zap size={18} />
            </div>
            <h4 className="text-xs font-semibold text-text-primary mb-1">2. Live Stream</h4>
            <p className="text-[10px] text-text-muted leading-normal">Pull live Cost Explorer data directly from AWS.</p>
          </div>
          <div className="p-4 rounded-lg bg-background-secondary/30 border border-border-primary">
            <div className="text-accent-primary mb-2">
              <ArrowRight size={18} />
            </div>
            <h4 className="text-xs font-semibold text-text-primary mb-1">3. Optimize</h4>
            <p className="text-[10px] text-text-muted leading-normal">Deploy rightsizing rules and save immediately.</p>
          </div>
        </div>

        <Button 
          onClick={() => navigate('/settings?tab=aws')}
          className="px-8 py-3 bg-gradient-to-r from-accent-primary to-indigo-500 hover:from-accent-primary/95 hover:to-indigo-500/95 font-semibold text-sm rounded-lg shadow-md hover:shadow-lg transition-all"
        >
          Connect AWS
        </Button>
      </CardContent>
    </Card>
  );
}
