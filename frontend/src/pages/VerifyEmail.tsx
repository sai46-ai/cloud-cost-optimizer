import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    // Simulate verification
    if (!token) {
      setStatus('error');
      return;
    }
    
    setTimeout(() => {
      setStatus('success');
    }, 1500);
  }, [token]);

  return (
    <div className="animate-fade-in text-center">
      {status === 'loading' && (
        <>
          <div className="w-16 h-16 mx-auto mb-6 flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h2 className="text-3xl font-bold text-text-primary mb-4">Verifying Email...</h2>
          <p className="text-text-secondary">Please wait while we verify your email address.</p>
        </>
      )}

      {status === 'success' && (
        <>
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={32} className="text-green-600" />
          </div>
          <h2 className="text-3xl font-bold text-text-primary mb-4">Email Verified!</h2>
          <p className="text-text-secondary mb-8">
            Your email address has been successfully verified. You can now access all features.
          </p>
          <Link to="/dashboard">
            <Button className="w-full py-5 text-base">Go to Dashboard</Button>
          </Link>
        </>
      )}

      {status === 'error' && (
        <>
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <XCircle size={32} className="text-red-600" />
          </div>
          <h2 className="text-3xl font-bold text-text-primary mb-4">Verification Failed</h2>
          <p className="text-text-secondary mb-8">
            The verification link is invalid or has expired. Please request a new verification email.
          </p>
          <Link to="/login">
            <Button className="w-full py-5 text-base">Back to Login</Button>
          </Link>
        </>
      )}
    </div>
  );
}
