import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { AuthCard, AuthInput, AuthButton } from '../components/auth/AuthUI';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setIsSent(true);
    }, 1000);
  };

  if (isSent) {
    return (
      <div className="animate-fade-in w-full text-center">
        <AuthCard>
          <div className="w-16 h-16 bg-accent-emerald/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={32} className="text-accent-emerald" />
          </div>
          <h2 className="text-3xl font-bold text-text-primary mb-4 tracking-tight">Check your email</h2>
          <p className="text-text-secondary mb-8 leading-relaxed">
            We've sent password reset instructions to <br/>
            <span className="font-medium text-text-primary">{email}</span>
          </p>
          <Link to="/login">
            <AuthButton>Back to Login</AuthButton>
          </Link>
        </AuthCard>
      </div>
    );
  }

  return (
    <div className="animate-fade-in w-full">
      <AuthCard>
        <Link to="/login" className="inline-flex items-center text-sm font-medium text-text-muted hover:text-text-primary mb-6 transition-colors">
          <ArrowLeft size={16} className="mr-2" /> Back
        </Link>
        
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-text-primary mb-2 tracking-tight">Forgot Password</h2>
          <p className="text-text-secondary">Enter your email address and we'll send you a link to reset your password.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">Email Address</label>
            <AuthInput 
              type="email" 
              required
              autoComplete="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={18} />}
            />
          </div>
          
          <div className="pt-2">
            <AuthButton type="submit" isLoading={isLoading} disabled={!email}>
              Send Reset Link
            </AuthButton>
          </div>
        </form>
      </AuthCard>
    </div>
  );
}
