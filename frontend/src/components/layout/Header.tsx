import { useState, useRef, useEffect } from 'react';
import { Search, Bell, Sun, Moon, Menu, LogOut, User, Settings, BellOff, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import useStore from '../../store';
import { anomalyService, budgetService } from '../../services/api';
import { formatCurrency } from '../../lib/utils';
import { AnimatePresence, motion } from 'framer-motion';

export default function Header() {
  const { theme, toggleTheme, toggleSidebar, user } = useStore();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState<any[]>([]);
  
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const [focusedIndex, setFocusedIndex] = useState(-1);
  const menuItemsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const avatarButtonRef = useRef<HTMLButtonElement>(null);

  // Focus navigation hooks
  useEffect(() => {
    if (!showUserMenu) {
      setFocusedIndex(-1);
    }
  }, [showUserMenu]);

  useEffect(() => {
    if (focusedIndex >= 0 && menuItemsRef.current[focusedIndex]) {
      menuItemsRef.current[focusedIndex]?.focus();
    }
  }, [focusedIndex]);

  const handleDropdownKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedIndex(prev => (prev + 1) % 5);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedIndex(prev => (prev - 1 + 5) % 5);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setShowUserMenu(false);
      avatarButtonRef.current?.focus();
    }
  };

  const handleAvatarKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setShowUserMenu(true);
      setFocusedIndex(0);
    }
  };

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard shortcut for command palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setIsCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Load real anomalies & budgets as notifications
  useEffect(() => {
    async function loadAlerts() {
      try {
        const [anomalyData, budgetData] = await Promise.all([
          anomalyService.getAnomalies(),
          budgetService.getBudgets()
        ]);
        
        const alerts: any[] = [];
        
        // Active anomalies
        const activeAnomalies = (anomalyData || []).filter((a: any) => !a.is_resolved);
        activeAnomalies.forEach((a: any) => {
          alerts.push({
            id: `anomaly-${a.id}`,
            type: 'anomaly',
            title: `Critical Spike: ${a.service}`,
            message: a.root_cause || a.details,
            severity: 'critical',
            time: new Date(a.date).toLocaleDateString([], { month: 'short', day: 'numeric' })
          });
        });

        // Budgets exceeded
        (budgetData || []).forEach((b: any) => {
          const pct = (b.spent / b.amount) * 100;
          if (pct >= 100) {
            alerts.push({
              id: `budget-${b.id}`,
              type: 'budget',
              title: `Budget Exceeded: ${b.name}`,
              message: `Spent ${formatCurrency(b.spent)} of ${formatCurrency(b.amount)}`,
              severity: 'high',
              time: 'Alert'
            });
          } else if (pct >= 90) {
            alerts.push({
              id: `budget-${b.id}`,
              type: 'budget',
              title: `Budget Warning: ${b.name}`,
              message: `Spent ${formatCurrency(b.spent)} (${pct.toFixed(0)}%) of ${formatCurrency(b.amount)}`,
              severity: 'warning',
              time: 'Warning'
            });
          }
        });

        setNotifications(alerts);
      } catch (e) {
        console.error("Failed to load alerts for header:", e);
      }
    }
    
    // Only load if authenticated
    const token = localStorage.getItem('access_token');
    if (token) {
      loadAlerts();
    }
  }, []);
  
  // Format the path into a readable title
  const title = location.pathname === '/' || location.pathname === '/dashboard'
    ? 'Dashboard' 
    : location.pathname.substring(1).split('-').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');

  const initials = user?.full_name 
    ? user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() 
    : 'U';

  const handleSignOut = () => {
    localStorage.removeItem('access_token');
    useStore.getState().setAuthenticated(false);
    useStore.getState().setUser(null);
    setShowUserMenu(false);
    navigate('/login');
  };

  const getBreadcrumbs = () => {
    const segments = location.pathname.split('/').filter(Boolean);
    if (segments.length === 0 || location.pathname === '/dashboard') {
      return (
        <div className="flex items-center gap-1.5 text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
          <span>Platform</span>
          <span>/</span>
          <span className="text-[var(--text-primary)] font-semibold">Dashboard</span>
        </div>
      );
    }
    
    return (
      <div className="flex items-center gap-1.5 text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
        <span>{location.pathname === '/settings' ? 'System' : 'Platform'}</span>
        <span>/</span>
        <span className="text-[var(--text-primary)] font-semibold">
          {segments.map(s => s.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')).join(' / ')}
        </span>
      </div>
    );
  };

  return (
    <header className="h-16 border-b border-border-primary bg-background-secondary/80 backdrop-blur-md sticky top-0 z-30 px-8 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button 
          className="md:hidden w-8 h-8 rounded-lg border border-border-primary flex items-center justify-center hover:bg-background-elevated text-text-secondary hover:text-text-primary transition-all cursor-pointer" 
          onClick={toggleSidebar}
          aria-label="Toggle Sidebar"
        >
          <Menu size={18} />
        </button>
        <div className="flex flex-col items-start select-none">
          {getBreadcrumbs()}
          <div className="flex items-center gap-2 mt-0.5">
            <h2 className="text-base font-bold leading-tight tracking-tight text-text-primary">{title}</h2>
            {user?.is_demo_mode && (
              <span 
                className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[9px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/25 shadow-[0_0_8px_rgba(245,158,11,0.08)] select-none"
                title="Showing sample cloud data for evaluation."
              >
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                Demo Mode
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div 
          className="hidden md:flex items-center gap-2.5 bg-background-primary border border-border-primary rounded-lg px-3 py-1.5 min-w-[250px] cursor-pointer hover:border-accent-primary/30 focus-within:border-accent-primary focus-within:ring-2 ring-accent-primary/10 transition-all duration-200" 
          onClick={() => setIsCommandPaletteOpen(true)}
        >
          <Search size={15} className="text-text-muted" />
          <input type="text" placeholder="Search pages, actions..." readOnly className="cursor-pointer bg-transparent border-none outline-none text-xs text-text-primary w-full placeholder:text-text-muted/70" />
          <kbd className="ml-2 text-[10px] bg-background-elevated px-1.5 py-0.5 rounded border border-border-primary text-text-muted font-mono font-semibold shadow-sm select-none">⌘K</kbd>
        </div>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button 
            className="w-9 h-9 rounded-lg border border-border-primary bg-background-elevated flex items-center justify-center text-text-secondary hover:bg-background-primary hover:text-text-primary transition-all cursor-pointer shadow-sm" 
            aria-label="Notifications"
            aria-expanded={showNotifications}
            aria-haspopup="true"
            onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false); }}
          >
            <div className="relative">
              <Bell size={18} />
              {notifications.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-red-500 rounded-full border border-background-elevated animate-pulse"></span>
              )}
            </div>
          </button>

          {showNotifications && (
            <div className="dropdown-menu notification-panel">
              <div className="notification-panel-header">
                <span className="text-text-primary font-bold">Alerts Center</span>
                <span className="text-[10px] text-accent-primary font-bold bg-accent-primary/10 px-2 py-0.5 rounded-full">{notifications.length} unresolved</span>
              </div>
              {notifications.length > 0 ? (
                <div className="divide-y divide-border-primary/45 max-h-[300px] overflow-y-auto">
                  {notifications.map((n) => (
                    <div key={n.id} className="p-3.5 hover:bg-background-secondary/60 transition-colors text-left cursor-pointer" onClick={() => { setShowNotifications(false); navigate(n.type === 'anomaly' ? '/ai-insights' : '/budgets'); }}>
                      <div className="flex justify-between items-start mb-1 gap-2">
                        <span className="font-semibold text-xs text-text-primary flex items-center gap-1.5">
                          {n.severity === 'critical' ? (
                            <AlertCircle size={13} className="text-red-500 shrink-0" />
                          ) : (
                            <AlertTriangle size={13} className="text-amber-500 shrink-0" />
                          )}
                          {n.title}
                        </span>
                        <span className="text-[9px] text-text-muted font-semibold whitespace-nowrap shrink-0">{n.time}</span>
                      </div>
                      <p className="text-[11px] text-text-secondary leading-normal">{n.message}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="notification-panel-empty py-10">
                  <BellOff size={22} className="mx-auto mb-2.5 opacity-30 text-text-muted" />
                  <p className="text-xs text-text-primary font-semibold">All quiet right now</p>
                  <p className="text-[10px] mt-1 text-text-muted leading-relaxed max-w-[200px] mx-auto">Active anomalies and budget overruns will appear here.</p>
                </div>
              )}
            </div>
          )}
        </div>

        <button 
          className="w-9 h-9 rounded-lg border border-border-primary bg-background-elevated flex items-center justify-center text-text-secondary hover:bg-background-primary hover:text-text-primary transition-all cursor-pointer shadow-sm" 
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            ref={avatarButtonRef}
            className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-[#FAFAFA] font-bold text-xs cursor-pointer shadow-sm border-2 border-transparent hover:border-accent-primary transition-all focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-1 focus:ring-offset-background-secondary"
            onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false); }}
            onKeyDown={handleAvatarKeyDown}
            aria-label="User profile menu"
            aria-expanded={showUserMenu}
            aria-haspopup="true"
          >
            {initials}
          </button>

          <AnimatePresence>
            {showUserMenu && (
              <motion.div
                role="menu"
                aria-label="User dropdown menu"
                initial={{ opacity: 0, scale: 0.96, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, y: -2 }}
                transition={{ duration: 0.15, ease: 'easeOut' }}
                onKeyDown={handleDropdownKeyDown}
                className="absolute right-0 mt-2 w-[270px] rounded-xl border border-border-primary bg-background-elevated shadow-xl p-2 z-50 origin-top-right select-none"
              >
                {/* User info section */}
                <div className="px-3 py-2.5 mb-1.5 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-[#FAFAFA] font-semibold shadow-sm shrink-0">
                    {initials}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="font-bold text-sm text-[var(--text-primary)] truncate leading-tight">{user?.full_name || 'User'}</div>
                    <div className="text-xs text-[var(--text-muted)] truncate mt-1" title={user?.email || ''}>{user?.email || ''}</div>
                  </div>
                </div>

                <div className="border-t border-border-primary/30 my-1.5" />

                {/* Menu items */}
                <div className="space-y-0.5">
                  <button
                    role="menuitem"
                    ref={el => { menuItemsRef.current[0] = el; }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all text-left outline-none cursor-pointer focus:bg-background-primary/50 focus:text-text-primary focus:ring-1 focus:ring-accent-primary/20 ${focusedIndex === 0 ? 'bg-background-primary/50 text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-background-primary/50'}`}
                    onClick={() => { navigate('/profile'); setShowUserMenu(false); }}
                  >
                    <User size={16} className="text-text-muted shrink-0" />
                    <span>Profile</span>
                  </button>

                  <button
                    role="menuitem"
                    ref={el => { menuItemsRef.current[1] = el; }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all text-left outline-none cursor-pointer focus:bg-background-primary/50 focus:text-text-primary focus:ring-1 focus:ring-accent-primary/20 ${focusedIndex === 1 ? 'bg-background-primary/50 text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-background-primary/50'}`}
                    onClick={() => { navigate('/settings'); setShowUserMenu(false); }}
                  >
                    <Settings size={16} className="text-text-muted shrink-0" />
                    <span>Settings</span>
                  </button>

                  <button
                    role="menuitem"
                    ref={el => { menuItemsRef.current[2] = el; }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all text-left outline-none cursor-pointer focus:bg-background-primary/50 focus:text-text-primary focus:ring-1 focus:ring-accent-primary/20 ${focusedIndex === 2 ? 'bg-background-primary/50 text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-background-primary/50'}`}
                    onClick={toggleTheme}
                  >
                    {theme === 'dark' ? (
                      <>
                        <Sun size={16} className="text-text-muted shrink-0" />
                        <span>Light Mode</span>
                      </>
                    ) : (
                      <>
                        <Moon size={16} className="text-text-muted shrink-0" />
                        <span>Dark Mode</span>
                      </>
                    )}
                  </button>

                  <button
                    role="menuitem"
                    ref={el => { menuItemsRef.current[3] = el; }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all text-left outline-none cursor-pointer focus:bg-background-primary/50 focus:text-text-primary focus:ring-1 focus:ring-accent-primary/20 ${focusedIndex === 3 ? 'bg-background-primary/50 text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-background-primary/50'}`}
                    onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false); }}
                  >
                    <Bell size={16} className="text-text-muted shrink-0" />
                    <span>Notifications</span>
                  </button>
                </div>

                <div className="border-t border-border-primary/30 my-1.5" />

                <button
                  role="menuitem"
                  ref={el => { menuItemsRef.current[4] = el; }}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all text-left outline-none cursor-pointer focus:bg-danger/10 focus:ring-1 focus:ring-danger/20 ${focusedIndex === 4 ? 'bg-danger/10 text-danger' : 'text-danger hover:bg-danger/10'}`}
                  onClick={handleSignOut}
                >
                  <LogOut size={16} className="shrink-0" />
                  <span>Sign Out</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Command Palette Modal */}
      <AnimatePresence>
        {isCommandPaletteOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur-sm p-4 pt-[15vh]"
            onClick={() => setIsCommandPaletteOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: -20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.98 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[var(--border-secondary)] bg-[var(--bg-tertiary)]">
                <Search size={20} className="text-[var(--text-muted)]" />
                <input
                  type="text"
                  placeholder="Search pages, actions, and services..."
                  className="w-full bg-transparent border-none outline-none text-[var(--text-primary)] text-sm placeholder-[var(--text-muted)] font-sans"
                  autoFocus
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <span className="text-[10px] bg-[var(--bg-input)] border border-[var(--border-primary)] px-2 py-0.5 rounded text-[var(--text-muted)]">ESC</span>
              </div>
              
              <div className="max-h-[350px] overflow-y-auto p-2">
                {/* Pages Section */}
                <div className="px-3 py-1.5 text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Navigation</div>
                <div className="space-y-0.5 mb-4">
                  {[
                    { label: 'Dashboard', path: '/dashboard', desc: 'Overview of cost analytics & anomalies' },
                    { label: 'Cost Analytics', path: '/analytics', desc: 'Detailed spending charts & service breakdown' },
                    { label: 'Resource Optimizer', path: '/resources', desc: 'AI rightsizing recommendations' },
                    { label: 'AI Insights Chat', path: '/ai-insights', desc: 'Chatbot and anomaly details' },
                    { label: 'Budgets & Alerts', path: '/budgets', desc: 'Threshold alerts & limits' },
                    { label: 'Reports', path: '/reports', desc: 'PDF / CSV compiled exports' },
                    { label: 'Settings', path: '/settings', desc: 'AWS integrations, alerts, and system setup' },
                    { label: 'Profile', path: '/profile', desc: 'User personal profile, security details, and statistics' },
                  ]
                    .filter(p => p.label.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map(item => (
                      <button
                        key={item.path}
                        className="w-full px-3 py-2 text-left rounded-lg hover:bg-[var(--bg-tertiary)] flex justify-between items-center group transition-colors"
                        onClick={() => {
                          navigate(item.path);
                          setIsCommandPaletteOpen(false);
                          setSearchQuery('');
                        }}
                      >
                        <div>
                          <div className="text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-primary)]">{item.label}</div>
                          <div className="text-xs text-[var(--text-muted)] mt-0.5">{item.desc}</div>
                        </div>
                        <span className="text-xs text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity">Go to ↵</span>
                      </button>
                    ))}
                </div>

                {/* Actions Section */}
                <div className="px-3 py-1.5 text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Quick Actions</div>
                <div className="space-y-0.5">
                  {[
                    { label: 'Toggle Dark/Light Mode', action: () => toggleTheme(), desc: `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode` },
                    { label: 'Sign Out', action: () => handleSignOut(), desc: 'Sign out of your active session' },
                  ]
                    .filter(a => a.label.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map((item, idx) => (
                      <button
                        key={idx}
                        className="w-full px-3 py-2 text-left rounded-lg hover:bg-[var(--bg-tertiary)] flex justify-between items-center group transition-colors"
                        onClick={() => {
                          item.action();
                          setIsCommandPaletteOpen(false);
                          setSearchQuery('');
                        }}
                      >
                        <div>
                          <div className="text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--accent-primary)]">{item.label}</div>
                          <div className="text-xs text-[var(--text-muted)] mt-0.5">{item.desc}</div>
                        </div>
                        <span className="text-xs text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity">Run ↵</span>
                      </button>
                    ))}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </header>
  );
}
