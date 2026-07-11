import React, { useEffect, useState, useCallback } from 'react';
import { adminService } from '../../services/api';
import useStore from '../../store';
import { 
  History, 
  ChevronLeft, 
  ChevronRight, 
  Info,
  Calendar,
  Layers,
  ShieldAlert
} from 'lucide-react';

export default function AdminAuditLogs() {
  const { addToast } = useStore();
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminService.getAdminAuditLogs(page, pageSize);
      setLogs(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (e: any) {
      addToast(e.message || "Failed to load audit logs", "error");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, addToast]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'reviewer_assigned':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'reviewer_removed':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'user_disabled':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'user_enabled':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'admin_login':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">Administrative Audit Trail</h1>
        <p className="text-sm text-text-secondary mt-1">Review security events, role modifications, and logins logged for platform compliance.</p>
      </div>

      {/* Main Container */}
      <div className="bg-background-secondary border border-border-primary rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-20 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border-primary/50 text-[10px] uppercase font-bold text-text-muted tracking-wider bg-background-elevated/25 select-none">
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Operator ID</th>
                  <th className="py-3.5 px-4">Resource Target</th>
                  <th className="py-3.5 px-4">Description</th>
                  <th className="py-3.5 px-6">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary/40 text-xs">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-background-elevated/15 transition-colors">
                    {/* Timestamp */}
                    <td className="py-4 px-6 text-text-secondary whitespace-nowrap font-medium flex items-center gap-2">
                      <Calendar size={13} className="text-text-muted shrink-0" />
                      {formatDateTime(log.created_at)}
                    </td>

                    {/* Action badge */}
                    <td className="py-4 px-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${getActionColor(log.action)}`}>
                        {log.action.replace('_', ' ')}
                      </span>
                    </td>

                    {/* Operator ID */}
                    <td className="py-4 px-4 text-text-secondary font-mono tracking-tight whitespace-nowrap">
                      {log.user_id ? log.user_id.substring(0, 8) + '...' : 'SYSTEM'}
                    </td>

                    {/* Target */}
                    <td className="py-4 px-4 text-text-secondary whitespace-nowrap flex items-center gap-1.5 mt-0.5">
                      <Layers size={13} className="text-text-muted shrink-0" />
                      <span className="font-semibold text-text-primary capitalize">{log.resource_type || "N/A"}</span>
                      {log.resource_id && (
                        <span className="text-[10px] text-text-muted font-mono">({log.resource_id.substring(0, 8)}...)</span>
                      )}
                    </td>

                    {/* Description */}
                    <td className="py-4 px-4 text-text-secondary leading-relaxed max-w-sm">
                      {log.description}
                    </td>

                    {/* IP */}
                    <td className="py-4 px-6 text-text-muted font-mono whitespace-nowrap">
                      {log.ip_address || "Unknown"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-20 text-center">
            <History size={36} className="mx-auto text-text-muted opacity-30 mb-3" />
            <span className="font-bold text-sm text-text-primary">No logs recorded</span>
            <p className="text-xs text-text-muted mt-1 leading-relaxed max-w-xs mx-auto">No administrative events have been recorded in the audit trail yet.</p>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="border-t border-border-primary/50 px-6 py-4 flex justify-between items-center select-none bg-background-elevated/10">
            <span className="text-xs text-text-muted font-medium">
              Showing <span className="font-bold text-text-primary">{logs.length}</span> of <span className="font-bold text-text-primary">{total}</span> events
            </span>

            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                className="w-8 h-8 rounded-lg border border-border-primary bg-background-elevated flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-background-primary transition-all cursor-pointer disabled:opacity-30 disabled:pointer-events-none shadow-sm"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                className="w-8 h-8 rounded-lg border border-border-primary bg-background-elevated flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-background-primary transition-all cursor-pointer disabled:opacity-30 disabled:pointer-events-none shadow-sm"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
