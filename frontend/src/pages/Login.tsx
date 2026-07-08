import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogIn, Mail, Lock, AlertCircle } from 'lucide-react';
import useStore from '../store';
import { authService } from '../services/api';
import { AuthCard, AuthInput, AuthButton } from '../components/auth/AuthUI';

export default function Login() {
  const navigate = useNavigate();
  const setAuthenticated = useStore((state) => state.setAuthenticated);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError('Email and password are required');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await authService.login({ email, password });
      
      // Save token
      localStorage.setItem('access_token', response.access_token);
      
      // Update global state
      useStore.getState().setUser(response.user);
      setAuthenticated(true);
      
      navigate('/dashboard');
    } catch (err: any) {
      console.error("Login failed:", err);
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in w-full">
      <AuthCard>
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2 tracking-tight">Welcome back</h1>
          <p className="text-text-secondary">Sign in to your CloudWise account to continue.</p>
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-xl flex items-start gap-3">
            <AlertCircle className="text-danger mt-0.5 flex-shrink-0" size={18} />
            <p className="text-sm text-danger">{error}</p>
          </div>
        )}
        
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
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-text-primary">Password</label>
              <Link 
                to="/forgot-password"
                className="text-sm font-medium text-blue-400 hover:text-blue-400-hover transition-colors bg-transparent border-none p-0 cursor-pointer outline-none"
              >
                Forgot password?
              </Link>
            </div>
            <AuthInput 
              type="password" 
              required
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={18} />}
            />
          </div>
          
          <div className="pt-2">
            <AuthButton type="submit" isLoading={isLoading}>
              Sign In <LogIn size={18} className="ml-1" />
            </AuthButton>
          </div>
        </form>
        
        <p className="mt-8 text-center text-sm text-text-secondary">
          Don't have an account? <Link to="/register" className="font-medium text-blue-400 hover:text-blue-400-hover transition-colors">Start your free trial</Link>
        </p>
      </AuthCard>
    </div>
  );
}
