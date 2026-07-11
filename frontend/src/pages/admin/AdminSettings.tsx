import React from 'react';
import { Settings, Info, ShieldAlert, Cpu, CheckCircle2, Server, HelpCircle } from 'lucide-react';
import useStore from '../../store';

export default function AdminSettings() {
  const { addToast } = useStore();

  const handleBackup = () => {
    addToast("Platform state snapshot backup initiated", "success");
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">System Settings</h1>
        <p className="text-sm text-text-secondary mt-1">Configure global parameters, verify credentials, and view system architecture details.</p>
      </div>

      {/* Production Readiness Checklist */}
      <div className="p-6 rounded-xl border border-amber-500/25 bg-amber-500/5 shadow-sm space-y-4">
        <div className="flex gap-3">
          <ShieldAlert size={20} className="text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="font-bold text-sm text-amber-400">Production Transition Alert</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              This application is running with development mode components active. Ensure you follow the architectural guidelines below before deploying this platform for customer review.
            </p>
          </div>
        </div>

        <div className="border-t border-amber-500/15 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5 p-3 rounded-lg bg-background-primary/40 border border-amber-500/10">
            <span className="text-[10px] font-extrabold uppercase text-amber-400">1. Disable Development Seed</span>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Set the environment variable <code className="px-1 py-0.5 rounded bg-background-elevated border border-border-primary text-rose-400 font-mono text-[10px]">SEED_DEV_ADMIN=False</code> to disable the default <code className="font-mono text-text-secondary text-[10px]">admin@gmail.com</code> account.
            </p>
          </div>
          <div className="space-y-1.5 p-3 rounded-lg bg-background-primary/40 border border-amber-500/10">
            <span className="text-[10px] font-extrabold uppercase text-amber-400">2. Rotate Secrets</span>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Generate a secure 256-bit secret key for <code className="font-mono text-text-secondary text-[10px]">SECRET_KEY</code> and ensure default JWT credentials are rotated.
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Core Config */}
        <div className="p-6 rounded-xl border border-border-primary bg-background-secondary shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border-primary/50 pb-3">
            <Settings size={16} className="text-accent-primary" />
            <span className="font-bold text-sm text-text-primary">Configuration Details</span>
          </div>

          <div className="space-y-3.5 text-xs text-text-secondary">
            <div className="flex justify-between items-center py-1">
              <span className="font-medium text-text-muted">Environment</span>
              <span className="font-bold text-text-primary uppercase text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20">Development</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="font-medium text-text-muted">Database Engine</span>
              <span className="font-semibold text-text-primary">SQLite v3 (WAL Mode)</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="font-medium text-text-muted">CORS Domain Restrictions</span>
              <span className="font-semibold text-text-primary text-[10px] bg-background-elevated px-2 py-0.5 border border-border-primary rounded">http://localhost:5173</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="font-medium text-text-muted">Default Role Policy</span>
              <span className="font-semibold text-text-primary uppercase text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20">USER (Default)</span>
            </div>
          </div>
        </div>

        {/* Maintenance Actions */}
        <div className="p-6 rounded-xl border border-border-primary bg-background-secondary shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border-primary/50 pb-3">
            <Server size={16} className="text-accent-primary" />
            <span className="font-bold text-sm text-text-primary">Maintenance Operations</span>
          </div>

          <div className="space-y-3.5">
            <p className="text-xs text-text-secondary leading-normal">
              Perform administrative operations to preserve and manage database storage and state snapshots.
            </p>
            <div className="space-y-2 pt-2">
              <button
                onClick={handleBackup}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-background-elevated border border-border-primary text-text-primary hover:bg-background-primary hover:border-accent-primary/20 transition-all cursor-pointer shadow-sm"
              >
                Create SQLite Backup
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* System info */}
      <div className="p-6 rounded-xl border border-border-primary bg-background-secondary shadow-sm space-y-4">
        <div className="flex items-center gap-2 border-b border-border-primary/50 pb-3">
          <Cpu size={16} className="text-accent-primary" />
          <span className="font-bold text-sm text-text-primary">Platform Diagnostics</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs text-center">
          <div className="p-3 bg-background-elevated/25 border border-border-primary/30 rounded-lg">
            <span className="text-[10px] uppercase font-bold text-text-muted block">React Framework</span>
            <span className="font-bold text-text-primary mt-1 block">v19.2.6</span>
          </div>
          <div className="p-3 bg-background-elevated/25 border border-border-primary/30 rounded-lg">
            <span className="text-[10px] uppercase font-bold text-text-muted block">FastAPI</span>
            <span className="font-bold text-text-primary mt-1 block">v0.115.0</span>
          </div>
          <div className="p-3 bg-background-elevated/25 border border-border-primary/30 rounded-lg">
            <span className="text-[10px] uppercase font-bold text-text-muted block">SQLAlchemy</span>
            <span className="font-bold text-text-primary mt-1 block">v2.0.35</span>
          </div>
          <div className="p-3 bg-background-elevated/25 border border-border-primary/30 rounded-lg">
            <span className="text-[10px] uppercase font-bold text-text-muted block">Vite Build Tool</span>
            <span className="font-bold text-text-primary mt-1 block">v8.0.12</span>
          </div>
        </div>
      </div>
    </div>
  );
}
