import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../../api/client';
import { 
  GitMerge, FileText, ShieldAlert, Activity, 
  Loader2, AlertCircle, ArrowRight, CheckCircle2, Network, Download
} from 'lucide-react';

export default function SupervisoryAnalyticsPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const isReportsView = location.pathname.includes('/reports');

  const [crossCaseData, setCrossCaseData] = useState(null);
  const [reportsData, setReportsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadSupervisoryData() {
      try {
        setLoading(true);
        setError(null);

        const [crossRes, reportsRes] = await Promise.all([
          api.get('/api/analytics/cross-case').catch(() => ({ data: {} })),
          api.get('/api/analytics/reports').catch(() => ({ data: {} }))
        ]);

        setCrossCaseData(crossRes.data);
        setReportsData(reportsRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load supervisory intelligence.');
      } finally {
        setLoading(false);
      }
    }

    loadSupervisoryData();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-amber-950/40 via-slate-900/90 to-slate-900 border border-amber-500/30 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold mb-3">
              <ShieldAlert size={13} />
              <span>IPS Supervisory Command Console</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
              Cross-Case & Community Bridging Intelligence
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Supervisory oversight identifying multi-jurisdictional syndicate nexus points, bridging operatives across cases, and executive summaries.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-950/80 border border-amber-500/30 rounded-xl text-amber-300 text-xs font-mono">
            <span>Access Tier: IPS Officer HQ</span>
          </div>
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-1">
        <button
          onClick={() => navigate('/supervisory/cross-case')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            !isReportsView
              ? 'bg-amber-500/20 text-amber-200 border border-amber-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <GitMerge size={14} />
          <span>Cross-Case Connectivity</span>
        </button>

        <button
          onClick={() => navigate('/supervisory/reports')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            isReportsView
              ? 'bg-amber-500/20 text-amber-200 border border-amber-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <FileText size={14} />
          <span>Executive Intelligence Reports</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 size={28} className="animate-spin text-amber-400" />
          <span className="text-xs">Correlating cross-case relational graphs…</span>
        </div>
      ) : !isReportsView ? (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Cross-Case Linkages
              </div>
              <div className="text-2xl font-bold text-amber-400 mt-2">
                {crossCaseData?.cross_case_connectivity?.length || '0'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Multi-case bridging entities</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Community Bridging Nodes
              </div>
              <div className="text-2xl font-bold text-indigo-400 mt-2">
                {crossCaseData?.community_bridging?.length || '0'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Clusters linked by common actors</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Total Monitored Communities
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-2">
                {crossCaseData?.communities_count || '0'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Active Louvain clusters</div>
            </div>
          </div>

          {/* Cross Case Entities Table */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <GitMerge size={15} className="text-amber-400" />
                Cross-Case Entities & Operatives
              </h3>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                AUTHORITATIVE IPS ENDPOINT
              </span>
            </div>

            <div className="space-y-3">
              {crossCaseData?.cross_case_connectivity?.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-slate-700 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-amber-400">
                        {item.entity_id}
                      </span>
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        Connected to {item.case_count} Cases
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-slate-400 mt-1 flex flex-wrap gap-1.5">
                      <span>Cases:</span>
                      {item.cases?.map((c) => (
                        <span key={c} className="text-indigo-300 bg-indigo-950/40 px-1.5 py-0.5 rounded border border-indigo-900/60">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => navigate(`/entities/${item.entity_id}`)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all flex items-center gap-1.5 cursor-pointer shrink-0 self-start sm:self-auto"
                  >
                    <span>View Dossier</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              )) || (
                <div className="text-xs text-slate-400 text-center py-8">
                  No cross-case entities discovered in active index.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Reports View */
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Executive Supervisory Report Brief
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Multi-case syndicate patterns generated under official supervision protocols.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
              {reportsData?.generated_status || 'CONFIDENTIAL'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Report Title</span>
              <span className="text-sm font-bold text-slate-100">{reportsData?.report_type || 'Executive Intelligence Brief'}</span>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Total Cross-Case Linkages</span>
              <span className="text-sm font-bold text-amber-400">{reportsData?.total_cross_case_links || '0'} verified connections</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
            <span className="font-bold text-slate-200">Top Bridging Operatives in Multi-District Syndicates:</span>
            <div className="space-y-1.5 pt-1">
              {reportsData?.top_bridging_entities?.map((bridge, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 flex items-center justify-between">
                  <span className="font-mono text-indigo-300 font-bold">{bridge.entity_id}</span>
                  <span className="text-[11px] text-slate-400">
                    Bridges communities: {bridge.communities_bridged?.join(', ') || 'Multi-cluster'}
                  </span>
                </div>
              )) || <div className="text-slate-400 text-xs">No bridging entities identified.</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
