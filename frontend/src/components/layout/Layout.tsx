import { Suspense } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info as InfoIcon } from 'lucide-react';
import Sidebar from './Sidebar';
import Header from './Header';
import PageTransition from './PageTransition';
import useStore from '../../store';

const PageFallback = () => (
  <div className="w-full h-full min-h-[400px] flex items-center justify-center">
    <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
  </div>
);

export default function Layout() {
  const { sidebarOpen, setSidebarOpen, sidebarCollapsed, toasts, removeToast } = useStore();
  const location = useLocation();

  return (
    <div className={`flex min-h-screen relative bg-background-primary transition-all duration-300 ${sidebarCollapsed ? 'collapsed-layout' : ''}`}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-[#111827]/60 backdrop-blur-sm z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      <Sidebar />
      
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${sidebarCollapsed ? 'md:ml-[68px]' : 'md:ml-[260px]'}`}>
        <Header />
        <main className="flex-1 p-8 max-w-[1400px] w-full mx-auto">
          <AnimatePresence mode="wait">
            <PageTransition key={location.pathname}>
              <Suspense fallback={<PageFallback />}>
                <Outlet />
              </Suspense>
            </PageTransition>
          </AnimatePresence>
        </main>
      </div>

      {/* Floating Toast Notification overlay */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95, transition: { duration: 0.15 } }}
              className={`flex items-center gap-3 p-4 rounded-xl border shadow-xl pointer-events-auto min-w-[280px] max-w-sm bg-[var(--bg-card)] ${
                toast.type === 'success'
                  ? 'border-green-500/25 bg-green-500/5 text-green-500'
                  : toast.type === 'error'
                  ? 'border-red-500/25 bg-red-500/5 text-red-500'
                  : toast.type === 'warning'
                  ? 'border-orange-500/25 bg-orange-500/5 text-orange-500'
                  : 'border-[var(--border-primary)] bg-[var(--bg-tertiary)] text-[var(--accent-primary)]'
              }`}
            >
              <div className="shrink-0">
                {toast.type === 'success' && <CheckCircle size={18} />}
                {toast.type === 'error' && <AlertCircle size={18} />}
                {toast.type === 'warning' && <AlertTriangle size={18} />}
                {toast.type === 'info' && <InfoIcon size={18} />}
              </div>
              
              <div className="flex-1 text-sm text-[var(--text-primary)] font-medium leading-tight">
                {toast.message}
              </div>
              
              <button
                onClick={() => removeToast(toast.id)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors p-0.5"
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
