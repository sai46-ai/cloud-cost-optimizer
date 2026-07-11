import React, { useEffect, useState, useCallback } from 'react';
import { adminService } from '../../services/api';
import useStore from '../../store';
import { 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Database,
  ArrowUpDown,
  Lock,
  Unlock,
  ShieldCheck,
  UserX
} from 'lucide-react';

export default function UserManagement() {
  const { user: currentUser, addToast } = useStore();
  
  // Queries
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [awsFilter, setAwsFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  
  // Data State
  const [users, setUsers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [actionPending, setActionPending] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const params: any = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      if (statusFilter) params.account_status = statusFilter;
      if (awsFilter) params.aws_connected = awsFilter === "yes";

      const data = await adminService.getUsers(params);
      setUsers(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (e: any) {
      addToast(e.message || "Failed to load users", "error");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, sortBy, sortOrder, search, roleFilter, statusFilter, awsFilter, addToast]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      setActionPending(userId);
      await adminService.updateRole(userId, newRole);
      addToast("User role updated successfully", "success");
      fetchUsers();
    } catch (e: any) {
      addToast(e.message || "Failed to update user role", "error");
    } finally {
      setActionPending(null);
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: string) => {
    try {
      setActionPending(userId);
      const targetStatus = currentStatus === "active" ? "disabled" : "active";
      await adminService.updateStatus(userId, targetStatus);
      addToast(`Account has been ${targetStatus === 'active' ? 'enabled' : 'disabled'}`, "success");
      fetchUsers();
    } catch (e: any) {
      addToast(e.message || "Failed to update account status", "error");
    } finally {
      setActionPending(null);
    }
  };

  const getInitials = (name: string) => {
    return name ? name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U';
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString(undefined, { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">User Directory</h1>
        <p className="text-sm text-text-secondary mt-1">Manage corporate access, promote reviewers, and control platform governance.</p>
      </div>

      {/* Query Bar */}
      <div className="bg-background-secondary border border-border-primary rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="w-full md:w-auto flex items-center gap-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search size={15} className="absolute left-3 top-3.5 text-text-muted" />
            <input
              type="text"
              placeholder="Search user name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs bg-background-primary border border-border-primary focus:border-accent-primary focus:ring-1 focus:ring-accent-primary/20 rounded-lg text-text-primary placeholder:text-text-muted/65 outline-none"
            />
          </div>
          <button 
            type="submit"
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-accent-primary hover:bg-accent-primary-hover text-[#FAFAFA] transition-colors cursor-pointer"
          >
            Find
          </button>
        </form>

        {/* Filters */}
        <div className="w-full md:w-auto flex flex-wrap items-center gap-3">
          {/* Role */}
          <div className="flex items-center gap-1.5 bg-background-primary border border-border-primary px-2.5 py-1.5 rounded-lg">
            <Filter size={12} className="text-text-muted" />
            <select
              value={roleFilter}
              onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
              className="bg-transparent border-none outline-none text-xs text-text-secondary font-medium cursor-pointer"
            >
              <option value="">All Roles</option>
              <option value="USER">USER</option>
              <option value="REVIEWER">REVIEWER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>

          {/* Account Status */}
          <div className="flex items-center gap-1.5 bg-background-primary border border-border-primary px-2.5 py-1.5 rounded-lg">
            <Filter size={12} className="text-text-muted" />
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-transparent border-none outline-none text-xs text-text-secondary font-medium cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>

          {/* AWS Connected */}
          <div className="flex items-center gap-1.5 bg-background-primary border border-border-primary px-2.5 py-1.5 rounded-lg">
            <Filter size={12} className="text-text-muted" />
            <select
              value={awsFilter}
              onChange={(e) => { setAwsFilter(e.target.value); setPage(1); }}
              className="bg-transparent border-none outline-none text-xs text-text-secondary font-medium cursor-pointer"
            >
              <option value="">All Integration States</option>
              <option value="yes">AWS Connected</option>
              <option value="no">AWS Not Connected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table container */}
      <div className="bg-background-secondary border border-border-primary rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-20 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border-primary/50 text-[10px] uppercase font-bold text-text-muted tracking-wider bg-background-elevated/25 select-none">
                  <th className="py-3.5 px-6">Avatar</th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-text-primary" onClick={() => toggleSort("full_name")}>
                    <span className="flex items-center gap-1">Name <ArrowUpDown size={11} /></span>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-text-primary" onClick={() => toggleSort("email")}>
                    <span className="flex items-center gap-1">Email <ArrowUpDown size={11} /></span>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-text-primary" onClick={() => toggleSort("role")}>
                    <span className="flex items-center gap-1">Role <ArrowUpDown size={11} /></span>
                  </th>
                  <th className="py-3.5 px-4">Reviewer Status</th>
                  <th className="py-3.5 px-4">AWS Connected</th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-text-primary" onClick={() => toggleSort("is_active")}>
                    <span className="flex items-center gap-1">Account Status <ArrowUpDown size={11} /></span>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-text-primary" onClick={() => toggleSort("created_at")}>
                    <span className="flex items-center gap-1">Created Date <ArrowUpDown size={11} /></span>
                  </th>
                  <th className="py-3.5 px-4 cursor-pointer hover:text-text-primary" onClick={() => toggleSort("last_login")}>
                    <span className="flex items-center gap-1">Last Login <ArrowUpDown size={11} /></span>
                  </th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary/40 text-xs">
                {users.map((u) => {
                  const isSelf = u.id === currentUser?.id;
                  const isReviewer = u.role === "REVIEWER";
                  
                  return (
                    <tr key={u.id} className="hover:bg-background-elevated/15 transition-colors">
                      {/* Avatar */}
                      <td className="py-4 px-6">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 border border-indigo-500/25 flex items-center justify-center font-bold text-text-primary text-[10px]">
                          {getInitials(u.full_name)}
                        </div>
                      </td>

                      {/* Name */}
                      <td className="py-4 px-4 font-semibold text-text-primary whitespace-nowrap">
                        {u.full_name} {isSelf && <span className="text-[9px] bg-accent-primary/10 text-accent-primary border border-accent-primary/20 px-1.5 py-0.5 rounded ml-1 font-bold">You</span>}
                      </td>

                      {/* Email */}
                      <td className="py-4 px-4 text-text-secondary whitespace-nowrap">{u.email}</td>

                      {/* Role Badge */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border border-current ${
                          u.role === 'ADMIN' 
                            ? 'bg-rose-500/10 text-rose-400' 
                            : u.role === 'REVIEWER' 
                            ? 'bg-amber-500/10 text-amber-400' 
                            : 'bg-blue-500/10 text-blue-400'
                        }`}>
                          {u.role}
                        </span>
                      </td>

                      {/* Reviewer Status */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 font-semibold text-[11px] ${isReviewer ? 'text-amber-400' : 'text-text-muted'}`}>
                          {isReviewer ? <ShieldCheck size={14} /> : null}
                          {isReviewer ? "Demo Mode (Reviewer)" : "Live Mode (Standard)"}
                        </span>
                      </td>

                      {/* AWS Connected */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${u.is_aws_connected ? 'text-emerald-400' : 'text-text-muted'}`}>
                          <Database size={13} />
                          {u.is_aws_connected ? "Connected" : "Not connected"}
                        </span>
                      </td>

                      {/* Account Status */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          u.account_status === 'active' 
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                            : 'bg-red-500/10 text-red-400 border-red-500/20'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${u.account_status === 'active' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                          {u.account_status === 'active' ? "Active" : "Disabled"}
                        </span>
                      </td>

                      {/* Created Date */}
                      <td className="py-4 px-4 text-text-muted whitespace-nowrap">{formatDate(u.created_at)}</td>

                      {/* Last Login */}
                      <td className="py-4 px-4 text-text-muted whitespace-nowrap">{u.last_login ? formatDate(u.last_login) : "Never"}</td>

                      {/* Actions */}
                      <td className="py-4 px-6 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2.5">
                          {/* Toggle Reviewer status */}
                          <button
                            disabled={isSelf || actionPending !== null}
                            onClick={() => handleRoleChange(u.id, isReviewer ? "USER" : "REVIEWER")}
                            title={isReviewer ? "Remove Reviewer status" : "Make Reviewer"}
                            className="p-1 text-text-secondary hover:text-amber-400 hover:bg-amber-400/5 rounded transition-all cursor-pointer disabled:opacity-30 disabled:pointer-events-none"
                          >
                            <ShieldCheck size={16} />
                          </button>

                          {/* Toggle Status active/disabled */}
                          <button
                            disabled={isSelf || actionPending !== null}
                            onClick={() => handleStatusToggle(u.id, u.account_status)}
                            title={u.account_status === "active" ? "Disable account" : "Enable account"}
                            className={`p-1 rounded transition-all cursor-pointer disabled:opacity-30 disabled:pointer-events-none ${
                              u.account_status === "active" 
                                ? 'text-text-secondary hover:text-red-400 hover:bg-red-400/5' 
                                : 'text-text-secondary hover:text-emerald-400 hover:bg-emerald-400/5'
                            }`}
                          >
                            {u.account_status === "active" ? <Lock size={15} /> : <Unlock size={15} />}
                          </button>

                          {/* Promote/demote Admin */}
                          <button
                            disabled={isSelf || actionPending !== null}
                            onClick={() => handleRoleChange(u.id, u.role === "ADMIN" ? "USER" : "ADMIN")}
                            title={u.role === "ADMIN" ? "Revoke Admin Privilege" : "Make Admin"}
                            className={`p-1 rounded transition-all cursor-pointer disabled:opacity-30 disabled:pointer-events-none ${
                              u.role === "ADMIN" 
                                ? 'text-text-secondary hover:text-rose-500 hover:bg-rose-500/5' 
                                : 'text-text-secondary hover:text-blue-400 hover:bg-blue-400/5'
                            }`}
                          >
                            <ShieldAlert size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-20 text-center">
            <UserX size={36} className="mx-auto text-text-muted opacity-30 mb-3" />
            <span className="font-bold text-sm text-text-primary">No members found</span>
            <p className="text-xs text-text-muted mt-1 leading-relaxed max-w-xs mx-auto">Try adjusting your filters or search terms.</p>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="border-t border-border-primary/50 px-6 py-4 flex justify-between items-center select-none bg-background-elevated/10">
            <span className="text-xs text-text-muted font-medium">
              Showing <span className="font-bold text-text-primary">{users.length}</span> of <span className="font-bold text-text-primary">{total}</span> members
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
