import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart3, 
  Server, 
  Sparkles, 
  Wallet, 
  FileText, 
  Settings,
  PanelLeftClose,
  Shield
} from 'lucide-react';
import useStore from '../../store';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/analytics', label: 'Cost Analytics', icon: BarChart3 },
  { path: '/resources', label: 'Resource Optimizer', icon: Server },
  { path: '/ai-insights', label: 'AI Insights', icon: Sparkles },
  { path: '/budgets', label: 'Budgets & Alerts', icon: Wallet },
  { path: '/reports', label: 'Reports', icon: FileText },
];

const bottomNavItems = [
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const { sidebarOpen, sidebarCollapsed, toggleSidebarCollapse, user } = useStore();

  const visibleNavItems = [...navItems];
  if (user?.role === 'ADMIN') {
    visibleNavItems.push({ path: '/admin/dashboard', label: 'Admin Panel', icon: Shield });
  }

  const initials = user?.full_name 
    ? user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() 
    : 'U';

  return (
    <aside
      aria-label="Main navigation"
      className={`fixed top-0 left-0 bottom-0 z-40 bg-background-secondary border-r border-border-primary flex flex-col transition-all duration-300 overflow-hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'} ${sidebarCollapsed ? 'w-[68px]' : 'w-[260px]'}`}>
      <div className="flex items-center gap-3 p-5 border-b border-border-primary bg-background-elevated/45">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-[#FAFAFA] font-bold text-sm shadow-[0_4px_14px_rgba(59,130,246,0.35)] shrink-0 select-none">CW</div>
        <div className={`transition-opacity duration-200 overflow-hidden ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>
          <div className="text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400 tracking-tight leading-tight">CloudWise AI</div>
          <span className="text-[9px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full tracking-wider uppercase">Enterprise</span>
        </div>
      </div>

      <nav aria-label="FinOps Platform navigation" className="flex-1 p-3 overflow-y-auto space-y-1.5 scrollbar-thin">
        <div className={`text-[10px] font-bold uppercase tracking-widest text-text-muted px-3 pt-3 pb-1 transition-opacity ${sidebarCollapsed ? 'opacity-0' : 'opacity-100'}`}>FinOps Platform</div>
        {visibleNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `relative flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 border ${
              isActive 
                ? 'bg-accent-primary/8 text-accent-primary border-accent-primary/15 shadow-sm' 
                : 'text-text-secondary border-transparent hover:bg-background-elevated/60 hover:text-text-primary'
            }`}
            title={sidebarCollapsed ? item.label : undefined}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-2.5 bottom-2.5 w-1 rounded-r-md bg-accent-primary" />
                )}
                <item.icon className={`w-[18px] h-[18px] shrink-0 ${sidebarCollapsed ? 'mx-auto' : ''} ${isActive ? 'text-accent-primary' : 'text-text-muted'}`} />
                <span className={`transition-opacity duration-200 whitespace-nowrap overflow-hidden ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>{item.label}</span>
              </>
            )}
          </NavLink>
        ))}

        <div className={`text-[10px] font-bold uppercase tracking-widest text-text-muted px-3 pt-6 pb-1 transition-opacity ${sidebarCollapsed ? 'opacity-0' : 'opacity-100'}`}>System</div>
        {bottomNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `relative flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 border ${
              isActive 
                ? 'bg-accent-primary/8 text-accent-primary border-accent-primary/15 shadow-sm' 
                : 'text-text-secondary border-transparent hover:bg-background-elevated/60 hover:text-text-primary'
            }`}
            title={sidebarCollapsed ? item.label : undefined}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-2.5 bottom-2.5 w-1 rounded-r-md bg-accent-primary" />
                )}
                <item.icon className={`w-[18px] h-[18px] shrink-0 ${sidebarCollapsed ? 'mx-auto' : ''} ${isActive ? 'text-accent-primary' : 'text-text-muted'}`} />
                <span className={`transition-opacity duration-200 whitespace-nowrap overflow-hidden ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle — desktop only */}
      <button 
        className="hidden md:flex items-center gap-3 p-4 text-text-muted hover:text-text-primary transition-colors border-t border-border-primary hover:bg-background-elevated/20 cursor-pointer" 
        onClick={toggleSidebarCollapse}
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        aria-expanded={!sidebarCollapsed}
        title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <PanelLeftClose size={16} className={`shrink-0 transition-transform duration-200 ${sidebarCollapsed ? 'mx-auto rotate-180' : ''}`} />
        <span className={`text-sm transition-opacity duration-200 overflow-hidden whitespace-nowrap ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>Collapse</span>
      </button>

      {/* User info section */}
      <div className="flex items-center gap-3 p-4 border-t border-border-primary bg-background-elevated/25">
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-[#FAFAFA] font-semibold text-sm shrink-0 shadow-inner select-none">{initials}</div>
        <div className={`transition-opacity duration-200 overflow-hidden whitespace-nowrap flex flex-col ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>
          <span className="text-sm font-semibold text-text-primary leading-none">{user?.full_name || 'User'}</span>
          <span className="text-[10px] text-text-muted mt-1">Enterprise • {user?.role || 'Member'}</span>
        </div>
      </div>
    </aside>
  );
}
