import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart3, 
  Server, 
  Sparkles, 
  Wallet, 
  FileText, 
  Settings,
  PanelLeftClose
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

  const initials = user?.full_name 
    ? user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() 
    : 'U';

  return (
    <aside className={`fixed top-0 left-0 bottom-0 z-40 bg-background-elevated border-r border-border-primary flex flex-col transition-all duration-300 overflow-hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'} ${sidebarCollapsed ? 'w-[68px]' : 'w-[260px]'}`}>
      <div className="flex items-center gap-3 p-6 border-b border-border-primary">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-[#FAFAFA] font-bold text-sm shadow-[0_0_20px_rgba(59,130,246,0.3)] shrink-0">CW</div>
        <div className={`transition-opacity duration-200 overflow-hidden ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>
          <div className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">CloudWise AI</div>
          <span className="text-[10px] font-semibold text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded-full tracking-wide">ENTERPRISE</span>
        </div>
      </div>

      <nav className="flex-1 p-4 overflow-y-auto space-y-1">
        <div className={`text-[11px] font-semibold uppercase tracking-widest text-text-muted px-3 pt-4 pb-2 transition-opacity ${sidebarCollapsed ? 'opacity-0' : 'opacity-100'}`}>FinOps Platform</div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-md font-medium text-sm transition-all duration-200 border ${isActive ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20' : 'text-text-secondary border-transparent hover:bg-[#111827]/5 dark:hover:bg-[#FAFAFA]/5 hover:text-text-primary'}`}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <item.icon className={`w-[18px] h-[18px] shrink-0 ${sidebarCollapsed ? 'mx-auto' : ''}`} />
            <span className={`transition-opacity duration-200 whitespace-nowrap overflow-hidden ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>{item.label}</span>
          </NavLink>
        ))}

        <div className={`text-[11px] font-semibold uppercase tracking-widest text-text-muted px-3 pt-8 pb-2 transition-opacity ${sidebarCollapsed ? 'opacity-0' : 'opacity-100'}`}>System</div>
        {bottomNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-md font-medium text-sm transition-all duration-200 border ${isActive ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20' : 'text-text-secondary border-transparent hover:bg-[#111827]/5 dark:hover:bg-[#FAFAFA]/5 hover:text-text-primary'}`}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <item.icon className={`w-[18px] h-[18px] shrink-0 ${sidebarCollapsed ? 'mx-auto' : ''}`} />
            <span className={`transition-opacity duration-200 whitespace-nowrap overflow-hidden ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle — desktop only */}
      <button 
        className="hidden md:flex items-center gap-3 p-4 text-text-muted hover:text-text-primary transition-colors border-t border-border-primary" 
        onClick={toggleSidebarCollapse}
        title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <PanelLeftClose size={16} className={`shrink-0 ${sidebarCollapsed ? 'mx-auto' : ''}`} />
        <span className={`text-sm transition-opacity duration-200 overflow-hidden whitespace-nowrap ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>Collapse</span>
      </button>

      {/* User info section */}
      <div className="flex items-center gap-3 p-4 border-t border-border-primary">
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-[#FAFAFA] font-medium text-sm shrink-0">{initials}</div>
        <div className={`transition-opacity duration-200 overflow-hidden whitespace-nowrap flex flex-col ${sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>
          <span className="text-sm font-semibold text-text-primary">{user?.full_name || 'User'}</span>
          <span className="text-xs text-text-muted">Enterprise • {user?.role || 'Member'}</span>
        </div>
      </div>
    </aside>
  );
}
