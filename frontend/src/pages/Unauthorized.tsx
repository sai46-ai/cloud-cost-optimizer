import { Link } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { Button } from '../components/ui/Button';

export default function Unauthorized() {
  return (
    <div className="animate-fade-in text-center">
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <ShieldAlert size={32} className="text-red-600" />
      </div>
      <h2 className="text-3xl font-bold text-text-primary mb-4">Access Denied</h2>
      <p className="text-text-secondary mb-8">
        You do not have permission to view this page. Please contact your administrator if you believe this is a mistake.
      </p>
      <Link to="/dashboard">
        <Button className="w-full py-5 text-base">Return to Dashboard</Button>
      </Link>
    </div>
  );
}
