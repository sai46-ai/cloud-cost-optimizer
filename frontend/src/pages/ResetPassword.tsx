import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, CheckCircle2 } from 'lucide-react';
import { AuthCard, AuthInput, AuthButton } from '../components/auth/AuthUI';

export default function ResetPassword() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) return;
    
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setIsSuccess(true);
    }, 1000);
  };

  if (isSuccess) {
    return (
      <div className="animate-fade-in w-full text-center">
        <AuthCard>
          <div className="w-16 h-16 bg-accent-emerald/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={32} className="text-accent-emerald" />
          </div>
          <h2 className="text-3xl font-bold text-text-primary mb-4 tracking-tight">Password reset!</h2>
          <p className="text-text-secondary mb-8 leading-relaxed">
            Your password has been successfully reset. You can now log in with your new password.
          </p>
          <Link to="/login">
            <AuthButton>Go to Login</AuthButton>
          </Link>
        </AuthCard>
      </div>
    );
  }

  return (
    <div className="animate-fade-in w-full">
      <AuthCard>
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-text-primary mb-2 tracking-tight">Create New Password</h2>
          <p className="text-text-secondary">Please enter your new password below.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">New Password</label>
            <AuthInput 
              type="password" 
              required
              autoComplete="new-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={18} />}
            />
            <p className="text-[13px] text-text-muted mt-1.5 ml-1">Must be at least 8 characters.</p>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">Confirm Password</label>
            <AuthInput 
              type="password" 
              required
              autoComplete="new-password"
              className={confirmPassword && password !== confirmPassword ? 'border-danger focus-visible:border-danger focus-visible:ring-danger/30' : ''} 
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              icon={<Lock size={18} />}
            />
            {confirmPassword && password !== confirmPassword && (
              <p className="text-[13px] text-danger mt-1.5 ml-1">Passwords do not match.</p>
            )}
          </div>
          
          <div className="pt-2">
            <AuthButton 
              type="submit" 
              disabled={isLoading || !password || password !== confirmPassword}
              isLoading={isLoading}
            >
              Reset Password
            </AuthButton>
          </div>
        </form>
      </AuthCard>
    </div>
  );
}
