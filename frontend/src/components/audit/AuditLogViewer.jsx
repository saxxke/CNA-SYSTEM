import React, { useState, useEffect, useCallback } from 'react';
import api from '../../api/client';
import { 
  Shield, AlertTriangle, CheckCircle2, XCircle, Search, 
  RefreshCw, Filter, Clock, User, Database, Lock, ArrowUpDown
} from 'lucide-react';

const EVENT_TYPE_OPTIONS = [
  { value: '', label: 'All Event Types' },
  { value: 'AUTH_LOGIN_SUCCESS', label: 'Login Success' },
  { value: 'AUTH_LOGIN_FAILURE', label: 'Login Failure' },
  { value: 'AUTH_LOGOUT', label: 'Logout' },
  { value: 'CASE_VIEW_DOSSIER', label: 'Case Dossier View' },
  { value: 'CASE_VIEW_GRAPH', label: 'Case Graph View' },
  { value: 'CASE_REGISTER', label: 'Case Registration' },
  { value: 'PERSON_VIEW_DOSSIER', label: 'Person Dossier View' },
  { value: 'ENTITY_VIEW', label: 'Entity Profile View' },
  { value: 'FAMILY_VIEW_PROFILE', label: 'Family Profile View' },
  { value: 'SEARCH_EXECUTE', label: 'Investigation Search' },
  { value: 'PRIORITY_LEADS_VIEW', label: 'Priority Leads View' },
  { value: 'ASSISTANT_QUERY', label: 'AI Assistant Query' },
  { value: 'CROSS_CASE_ANALYTICS_VIEW', label: 'Cross-Case Analytics View' },
  { value: 'CITIZEN_CASE_VIEW', label: 'Citizen Portal Access' },
  { value: 'UNAUTHORIZED_ACCESS_DENIED', label: 'Access Denied (401/403)' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'SUCCESS', label: 'SUCCESS' },
  { value: 'DENIED', label: 'DENIED' },
  { value: 'FAILED', label: 'FAILED' },
];

export default function AuditLogViewer() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [eventType, setEventType] = useState('');
  const [status, setStatus] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [targetIdFilter, setTargetIdFilter] = useState('');
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);

  const fetchAuditLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        limit,
        offset,
      };
      if (eventType) params.event_type = eventType;
      if (status) params.status = status;
      if (userIdFilter.trim()) params.user_id = userIdFilter.trim();
      if (targetIdFilter.trim()) params.target_id = targetIdFilter.trim();

      const response = await api.get('/api/audit/logs', { params });
      const rawEvents = response.data.events || response.data.items || [];
      const rawTotal = response.data.total_count ?? response.data.total ?? 0;
      setLogs(rawEvents);
      setTotal(rawTotal);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to retrieve immutable audit logs.');
    } finally {
      setLoading(false);
    }
  }, [eventType, status, userIdFilter, targetIdFilter, limit, offset]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  const handleResetFilters = () => {
    setEventType('');
    setStatus('');
    setUserIdFilter('');
    setTargetIdFilter('');
    setOffset(0);
  };

  const getStatusBadge = (logStatus, statusCode) => {
    if (logStatus === 'SUCCESS') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          <CheckCircle2 size={12} />
          {logStatus} ({statusCode})
        </span>
      );
    }
    if (logStatus === 'DENIED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
          <XCircle size={12} />
          {logStatus} ({statusCode})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
        <AlertTriangle size={12} />
        {logStatus} ({statusCode})
      </span>
    );
  };

  const getEventTypeBadge = (type) => {
    if (type.includes('DENIED')) {
      return 'bg-red-950/40 text-rose-300 border-rose-600/40';
    }
    if (type.startsWith('AUTH_')) {
      return 'bg-blue-950/40 text-blue-300 border-blue-600/40';
    }
    if (type.startsWith('CASE_')) {
      return 'bg-indigo-950/40 text-indigo-300 border-indigo-600/40';
    }
    if (type.startsWith('ASSISTANT_')) {
      return 'bg-purple-950/40 text-purple-300 border-purple-600/40';
    }
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  return (
    <div className="space-y-6">
      {/* Overview & Security Notice */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/60 rounded-xl p-5 shadow-lg relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400 shrink-0">
              <Shield size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-100">Immutable Audit Trail & Compliance Log</h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-700/80 text-amber-300 border border-amber-500/20">
                  Read-Only
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                Cryptographically verifiable, thread-safe access records tracking sensitive investigative actions, authentication, cross-case queries, and unauthorized intrusion denials. Server-authoritative actor identity; retention capped at 5,000 events.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-center">
            <button
              onClick={fetchAuditLogs}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-600 transition shadow-sm"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <Lock size={13} className="text-emerald-400" />
            <span>Server-side Authoritative</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Database size={13} className="text-indigo-400" />
            <span>Total Events: <strong className="text-slate-200">{total}</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock size={13} className="text-amber-400" />
            <span>Max Window: 5,000 events</span>
          </div>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-300 border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-indigo-400" />
            <span>Log Filter Parameters</span>
          </div>
          <button
            onClick={handleResetFilters}
            className="text-slate-400 hover:text-slate-200 text-xs transition"
          >
            Clear Filters
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Event Type */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Event Type</label>
            <select
              value={eventType}
              onChange={(e) => { setEventType(e.target.value); setOffset(0); }}
              className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {EVENT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setOffset(0); }}
              className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* User ID / Actor */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Actor / User ID</label>
            <input
              type="text"
              placeholder="e.g. io_sharma, citizen_1"
              value={userIdFilter}
              onChange={(e) => { setUserIdFilter(e.target.value); setOffset(0); }}
              className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Target ID */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Target ID</label>
            <input
              type="text"
              placeholder="e.g. CASE-084, ENT-102"
              value={targetIdFilter}
              onChange={(e) => { setTargetIdFilter(e.target.value); setOffset(0); }}
              className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-300 text-xs">
          <AlertTriangle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-950/70 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Target</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Outcome</th>
                <th className="py-3 px-4">Details / Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {loading && logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center gap-2">
                      <RefreshCw size={20} className="animate-spin text-indigo-400" />
                      <span>Loading immutable audit records...</span>
                    </div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500">
                    No audit records match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.event_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400 font-mono text-[11px]">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString('en-IN', { timeZone: 'UTC' }) : '-'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium border ${getEventTypeBadge(log.event_type)}`}>
                        {log.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-200">{log.actor_username || log.actor_user_id}</span>
                        <span className="text-[10px] text-slate-400">
                          {log.actor_role} {log.actor_jurisdiction ? `(${log.actor_jurisdiction})` : ''}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <span className="font-mono text-indigo-300 font-medium">{log.target_id || '-'}</span>
                        <span className="text-[10px] text-slate-500 uppercase">{log.target_type}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-slate-300 font-medium">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getStatusBadge(log.status, log.status_code)}
                    </td>
                    <td className="py-3 px-4 text-slate-400 max-w-xs truncate text-[11px]">
                      {log.details ? (
                        <span title={JSON.stringify(log.details)}>
                          {Object.entries(log.details)
                            .map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : v}`)
                            .join(', ')}
                        </span>
                      ) : (
                        <span className="text-slate-600">-</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination bar */}
        <div className="bg-slate-950/70 border-t border-slate-800 px-4 py-3 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="font-medium text-slate-200">{logs.length > 0 ? offset + 1 : 0}</span> to{' '}
            <span className="font-medium text-slate-200">{Math.min(offset + limit, total)}</span> of{' '}
            <span className="font-medium text-slate-200">{total}</span> records
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOffset((prev) => Math.max(0, prev - limit))}
              disabled={offset === 0 || loading}
              className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset((prev) => prev + limit)}
              disabled={offset + limit >= total || loading}
              className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
