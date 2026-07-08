import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Mail, Lock, Building, User, AlertCircle } from 'lucide-react';
import useStore from '../store';
import { authService } from '../services/api';
import { AuthCard, AuthInput, AuthButton } from '../components/auth/AuthUI';

export default function Register() {
  const navigate = useNavigate();
  const setAuthenticated = useStore((state) => state.setAuthenticated);
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const response = await authService.register({ 
        email: formData.email, 
        password: formData.password,
        full_name: formData.name,
        organization_name: formData.company
      });
      
      // Save token
      localStorage.setItem('access_token', response.access_token);
      
      // Update global state
      useStore.getState().setUser(response.user);
      setAuthenticated(true);
      
      navigate('/dashboard');
    } catch (err: any) {
      console.error("Registration failed:", err);
      setError(err.message || 'Failed to create account');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in w-full">
      <AuthCard>
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-text-primary mb-2 tracking-tight">Create an account</h2>
          <p className="text-text-secondary">Start optimizing your cloud costs in minutes.</p>
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-xl flex items-start gap-3">
            <AlertCircle className="text-danger mt-0.5 flex-shrink-0" size={18} />
            <p className="text-sm text-danger">{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-primary">Full Name</label>
              <AuthInput 
                type="text" 
                required
                autoComplete="name"
                placeholder="Enter your name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                icon={<User size={18} />}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-primary">Company</label>
              <AuthInput 
                type="text" 
                required
                autoComplete="organization"
                placeholder="Company Name"
                value={formData.company}
                onChange={(e) => setFormData({...formData, company: e.target.value})}
                icon={<Building size={18} />}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">Work Email</label>
            <AuthInput 
              type="email" 
              required
              autoComplete="email"
              placeholder="you@company.com"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              icon={<Mail size={18} />}
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">Password</label>
            <AuthInput 
              type="password" 
              required
              autoComplete="new-password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              icon={<Lock size={18} />}
            />
            <p className="text-[13px] text-text-muted mt-1.5 ml-1">Must be at least 8 characters.</p>
          </div>
          
          <div className="pt-2">
            <AuthButton type="submit" isLoading={isLoading}>
              Create Account <UserPlus size={18} className="ml-1" />
            </AuthButton>
          </div>
        </form>
        
        <p className="mt-8 text-center text-sm text-text-secondary">
          Already have an account? <Link to="/login" className="font-medium text-blue-400 hover:text-blue-400-hover transition-colors">Log in</Link>
        </p>
      </AuthCard>
    </div>
  );
}
