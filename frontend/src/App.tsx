import React, { Suspense, useEffect, useState, useRef, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Canvas } from '@react-three/fiber';
import { View } from '@react-three/drei';
import { isWebGLAvailable } from './lib/utils';
import Layout from './components/layout/Layout';
import AuthLayout from './components/layout/AuthLayout';
import useStore from './store';
import { 
  authService, 
  costService, 
  budgetService, 
  recommendationService, 
  anomalyService, 
  aiService, 
  reportService, 
  settingsService 
} from './services/api';

const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const ForgotPassword = React.lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = React.lazy(() => import('./pages/ResetPassword'));
const VerifyEmail = React.lazy(() => import('./pages/VerifyEmail'));

const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const CostAnalytics = React.lazy(() => import('./pages/CostAnalytics'));
const Resources = React.lazy(() => import('./pages/Resources'));
const AIInsights = React.lazy(() => import('./pages/AIInsights'));
const Budgets = React.lazy(() => import('./pages/Budgets'));
const Reports = React.lazy(() => import('./pages/Reports'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Profile = React.lazy(() => import('./pages/Profile'));
const Landing = React.lazy(() => import('./pages/Landing'));

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useStore((state) => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};


// Global Offline Banner
const OfflineBanner = () => {
  const isOffline = useStore((state) => state.isOffline);
  if (!isOffline) return null;
  
  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-white text-xs font-semibold px-4 py-1.5 text-center shadow-md">
      Connecting to server... You are currently in offline mode.
    </div>
  );
};

function App() {
  const containerRef = useRef<HTMLDivElement>(null!);
  const hasWebGL = useMemo(() => isWebGLAvailable(), []);
  const { theme, setAuthenticated, setUser, setOffline } = useStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    root.setAttribute('data-theme', theme);
  }, [theme]);

  // Global offline/online listeners
  useEffect(() => {
    const handleOffline = () => setOffline(true);
    const handleOnline = () => setOffline(false);
    
    window.addEventListener('api-offline', handleOffline);
    window.addEventListener('api-online', handleOnline);
    
    return () => {
      window.removeEventListener('api-offline', handleOffline);
      window.removeEventListener('api-online', handleOnline);
    };
  }, [setOffline]);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const profile = await authService.getProfile();
          setUser(profile);
          setAuthenticated(true);
          setOffline(false);
        } catch (e: any) {
          console.warn("Auth init failed, checking status:", e.message, e.status);
          if (e.status === 401 || e.status === 403) {
            localStorage.removeItem('access_token');
            setAuthenticated(false);
            setUser(null);
          } else {
            setOffline(true);
            setAuthenticated(true);
          }
        }
      }
      setIsInitializing(false);
    };
    
    initAuth();
  }, [setAuthenticated, setUser, setOffline]);

  // 3-Phase Staggered Prewarming System
  const isAuthenticated = useStore((state) => state.isAuthenticated);
  useEffect(() => {
    if (!isAuthenticated) return;

    let isCancelled = false;

    const prewarmData = async () => {
      try {
        // Phase 1: Critical dashboard data
        if (isCancelled) return;
        await costService.getDashboard();

        // Stagger Phase 2 by 200ms to prevent API saturation
        await new Promise<void>((resolve) => {
          const timer = setTimeout(resolve, 200);
          if (isCancelled) {
            clearTimeout(timer);
            resolve();
          }
        });

        // Phase 2: Core analytics data
        if (isCancelled) return;
        const today = new Date();
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(today.getDate() - 30);
        const startStr = thirtyDaysAgo.toISOString().split('T')[0];
        const endStr = today.toISOString().split('T')[0];

        await Promise.all([
          costService.getBreakdown(startStr, endStr),
          costService.getCosts(startStr, endStr),
        ]);

        // Stagger Phase 3 by 300ms
        await new Promise<void>((resolve) => {
          const timer = setTimeout(resolve, 300);
          if (isCancelled) {
            clearTimeout(timer);
            resolve();
          }
        });

        // Phase 3: Secondary operations
        if (isCancelled) return;
        await Promise.all([
          budgetService.getBudgets(),
          recommendationService.getRecommendations(),
          recommendationService.getSummary(),
          anomalyService.getAnomalies(),
          aiService.getForecasts(),
          reportService.getReports(),
          settingsService.getSettings(),
          settingsService.getAWSAccount(),
        ]);
      } catch (err) {
        console.warn("Prewarming was cancelled or failed:", err);
      }
    };

    prewarmData();

    return () => {
      isCancelled = true;
    };
  }, [isAuthenticated]);

  if (isInitializing) {
    return <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-primary)]">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>;
  }

  return (
    <div ref={containerRef} className="relative min-h-screen">
      <Router>
        <OfflineBanner />
        <Suspense fallback={
          <div className="h-screen w-screen flex items-center justify-center bg-[var(--bg-primary)]">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        }>
          <Routes>
            {/* Public Authentication Routes */}
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/verify" element={<VerifyEmail />} />
            </Route>

            {/* Public Landing Route */}
            <Route path="/" element={<Landing />} />

            {/* Protected Dashboard Routes */}
            <Route element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analytics" element={<CostAnalytics />} />
              <Route path="/resources" element={<Resources />} />
              <Route path="/ai-insights" element={<AIInsights />} />
              <Route path="/budgets" element={<Budgets />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Router>

      {hasWebGL && (
        <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
          <Canvas 
            eventSource={containerRef} 
            gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
            style={{ pointerEvents: 'none' }}
          >
            <View.Port />
          </Canvas>
        </div>
      )}
    </div>
  );
}

export default App;
