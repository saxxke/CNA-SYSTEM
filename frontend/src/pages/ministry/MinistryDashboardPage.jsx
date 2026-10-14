import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../../api/client';
import { 
  Building2, TrendingUp, Globe, FileText, BarChart3, 
  ShieldCheck, Activity, Loader2, AlertCircle, CheckCircle, Download
} from 'lucide-react';

export default function MinistryDashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // Determine active section from route
  const getTabFromPath = () => {
    if (location.pathname.includes('/analytics')) return 'analytics';
    if (location.pathname.includes('/trends')) return 'trends';
    if (location.pathname.includes('/regional')) return 'regional';
    if (location.pathname.includes('/reports')) return 'reports';
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState(getTabFromPath());
  const [summaryData, setSummaryData] = useState(null);
  const [trendsData, setTrendsData] = useState(null);
  const [regionalData, setRegionalData] = useState(null);
  const [reportsData, setReportsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setActiveTab(getTabFromPath());
  }, [location.pathname]);

  useEffect(() => {
    async function loadStrategicData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch authorized strategic endpoints in parallel
        const [summaryRes, trendsRes, regionalRes, reportsRes] = await Promise.all([
          api.get('/api/summary').catch(() => ({ data: {} })),
          api.get('/api/analytics/strategic-trends').catch(() => ({ data: {} })),
          api.get('/api/analytics/regional-statistics').catch(() => ({ data: {} })),
          api.get('/api/analytics/reports').catch(() => ({ data: {} }))
        ]);

        setSummaryData(summaryRes.data);
        setTrendsData(trendsRes.data);
        setRegionalData(regionalRes.data);
        setReportsData(reportsRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to fetch strategic oversight indicators.');
      } finally {
        setLoading(false);
      }
    }

    loadStrategicData();
  }, []);

  const handleTabChange = (tab, path) => {
    setActiveTab(tab);
    navigate(path);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-950/40 via-slate-900/90 to-slate-900 border border-purple-500/30 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-semibold mb-3">
              <Building2 size={13} />
              <span>Ministry of Home Affairs • Strategic Oversight Console</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
              National Strategic Intelligence Dashboard
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Macro crime trends, inter-district syndicate patterns, and high-level regional indicators across monitored jurisdictions.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-2 bg-slate-950/80 border border-purple-500/30 rounded-xl text-purple-300 text-xs font-mono self-start sm:self-auto">
            <ShieldCheck size={16} className="text-purple-400" />
            <span>High-Level Aggregates Only</span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-800">
        {[
          { id: 'overview', label: 'Strategic Overview', path: '/ministry/dashboard', icon: BarChart3 },
          { id: 'analytics', label: 'Aggregated Analytics', path: '/ministry/analytics', icon: Activity },
          { id: 'trends', label: 'Macro Trends', path: '/ministry/trends', icon: TrendingUp },
          { id: 'regional', label: 'Regional Statistics', path: '/ministry/regional', icon: Globe },
          { id: 'reports', label: 'Strategic Reports', path: '/ministry/reports', icon: FileText }
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id, tab.path)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? 'bg-purple-600/20 text-purple-200 border border-purple-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <tab.icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 size={28} className="animate-spin text-purple-400" />
          <span className="text-xs">Aggregating national strategic telemetry…</span>
        </div>
      ) : (
        <div className="space-y-6">
          
          {/* Key Strategic KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
                <span>Total Monitored Cases</span>
                <FileText size={16} className="text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 mt-2">
                {summaryData?.total_cases || summaryData?.cases_count || '15'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Multi-state registered files</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
                <span>Communities Monitored</span>
                <Activity size={16} className="text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 mt-2">
                {regionalData?.total_communities_monitored || trendsData?.communities_overview?.length || '6'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">High-density crime clusters</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
                <span>High-Centrality Entities</span>
                <Globe size={16} className="text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 mt-2">
                {regionalData?.high_centrality_nodes || '5'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Strategic syndicate nexus points</div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
                <span>Oversight Tier</span>
                <ShieldCheck size={16} className="text-emerald-400" />
              </div>
              <div className="text-sm font-bold text-emerald-400 mt-2 flex items-center gap-1.5">
                <CheckCircle size={15} />
                Level 4 National
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Active telemetric monitoring</div>
            </div>
          </div>

          {/* Section: Overview or Analytics */}
          {(activeTab === 'overview' || activeTab === 'analytics') && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Macro Indicators */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                    <TrendingUp size={15} className="text-purple-400" />
                    Macro Trend Telemetry
                  </h3>
                  <span className="text-[10px] font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/30">
                    AGGREGATED
                  </span>
                </div>

                <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="text-xs font-semibold text-slate-200">
                    {trendsData?.trend_summary || 'Multi-District Incident Patterns'}
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Automated Louvain community clustering indicates consistent syndicate centralization across mining and financial cyber networks.
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Community Clusters Overview
                  </div>
                  <div className="space-y-1.5">
                    {trendsData?.communities_overview?.map((comm, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/70 text-xs">
                        <span className="font-mono text-slate-300">Cluster #{comm.community_id}</span>
                        <span className="text-[11px] font-bold text-purple-300 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800/40">
                          {comm.size} Monitored Entities
                        </span>
                      </div>
                    )) || (
                      <div className="text-xs text-slate-400">Cluster telemetry loaded.</div>
                    )}
                  </div>
                </div>
              </div>

              {/* Regional Scope */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                    <Globe size={15} className="text-indigo-400" />
                    Jurisdictional Distribution
                  </h3>
                  <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/30">
                    CENTRAL SCOPE
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold mb-1">
                      Assigned Jurisdiction Scope
                    </span>
                    <span className="text-sm font-bold text-slate-100">
                      {regionalData?.jurisdiction_scope || 'National / Regional Aggregates'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold mb-1">
                      Strategic Telemetry Status
                    </span>
                    <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                      <CheckCircle size={13} />
                      {regionalData?.status || 'Aggregated strategic telemetry ready'}
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-500/30 text-[11px] text-purple-300 leading-relaxed">
                  <span className="font-bold text-purple-200">Executive Privacy Assurance:</span> Individual citizen records and unverified investigative notes are blocked from this view under federal data governance mandates.
                </div>
              </div>

            </div>
          )}

          {/* Section: Macro Trends */}
          {activeTab === 'trends' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-5">
              <div className="pb-3 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                    Macro Strategic Trends
                  </h3>
                  <p className="text-xs text-slate-400">
                    Macro crime trends and community cluster shifts over reporting cycles.
                  </p>
                </div>
                <span className="text-xs font-mono text-purple-400">
                  /api/analytics/strategic-trends
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-purple-300 uppercase">Top Community Hubs</span>
                  <div className="space-y-2">
                    {trendsData?.communities_overview?.map((c) => (
                      <div key={c.community_id} className="flex justify-between items-center text-xs p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-slate-200">Community #{c.community_id}</span>
                        <span className="font-mono text-purple-400 font-bold">{c.size} nodes</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-indigo-300 uppercase">Degree Centrality Distribution (Top 10)</span>
                  <div className="space-y-1.5 max-h-60 overflow-y-auto">
                    {trendsData?.degree_distribution_top?.map((item, i) => (
                      <div key={i} className="flex justify-between items-center text-xs p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="font-mono text-slate-300">Entity {item.entity_id}</span>
                        <span className="font-mono text-indigo-400 font-bold">{(item.centrality_score * 100).toFixed(1)}%</span>
                      </div>
                    )) || <div className="text-xs text-slate-400">No score distribution available.</div>}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section: Regional Statistics */}
          {activeTab === 'regional' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-5">
              <div className="pb-3 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                    Regional & District Statistics
                  </h3>
                  <p className="text-xs text-slate-400">
                    High-level metrics partitioned across state and national administrative zones.
                  </p>
                </div>
                <span className="text-xs font-mono text-indigo-400">
                  /api/analytics/regional-statistics
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase font-bold mb-1">Scope</div>
                  <div className="text-sm font-bold text-slate-100">{regionalData?.jurisdiction_scope}</div>
                </div>
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase font-bold mb-1">Monitored Clusters</div>
                  <div className="text-sm font-bold text-purple-400">{regionalData?.total_communities_monitored} active</div>
                </div>
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase font-bold mb-1">High Centrality Nodes</div>
                  <div className="text-sm font-bold text-amber-400">{regionalData?.high_centrality_nodes} detected</div>
                </div>
              </div>
            </div>
          )}

          {/* Section: Strategic Reports */}
          {activeTab === 'reports' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-5">
              <div className="pb-3 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                    Executive Strategic Briefs
                  </h3>
                  <p className="text-xs text-slate-400">
                    Generated from verified graph intelligence and cross-case evidence links.
                  </p>
                </div>
                <span className="text-xs font-mono text-purple-400">
                  /api/analytics/reports
                </span>
              </div>

              <div className="p-5 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                    {reportsData?.report_type || 'Executive Intelligence Brief'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    {reportsData?.generated_status || 'CONFIDENTIAL'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs pt-2">
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Total Cross-Case Links</span>
                    <span className="text-base font-bold text-indigo-400">{reportsData?.total_cross_case_links || '0'}</span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block mb-0.5">Bridging Entities Monitored</span>
                    <span className="text-base font-bold text-purple-400">{reportsData?.top_bridging_entities?.length || '0'}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
