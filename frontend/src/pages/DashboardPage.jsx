import React, { useState, useEffect } from 'react';
import { 
  Users, FolderOpen, Network, Bot, Search, BarChart3, 
  ArrowRight, ShieldCheck, ChevronRight, AlertCircle, 
  Layers, ExternalLink, Activity, FolderPlus
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import DashboardOverview from '../components/dashboard/DashboardOverview';
import TopLeads from '../components/dashboard/TopLeads';

const OFFENCE_BADGES = {
  'Cyber Crime': 'text-purple-300 bg-purple-950/80 border-purple-500/40',
  'Extortion': 'text-rose-300 bg-rose-950/80 border-rose-500/40',
  'Kidnapping': 'text-amber-300 bg-amber-950/80 border-amber-500/40',
  'Financial Fraud': 'text-emerald-300 bg-emerald-950/80 border-emerald-500/40',
  'Narcotics': 'text-red-300 bg-red-950/80 border-red-500/40',
  'Theft': 'text-blue-300 bg-blue-950/80 border-blue-500/40',
  'Homicide': 'text-stone-300 bg-stone-950/80 border-stone-500/40',
  'Smuggling': 'text-indigo-300 bg-indigo-950/80 border-indigo-500/40',
};

export default function DashboardPage() {
  const navigate = useNavigate();

  const [recentCases, setRecentCases] = useState([]);
  const [casesLoading, setCasesLoading] = useState(true);
  const [summaryData, setSummaryData] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchDashboardData = async () => {
      try {
        const [casesRes, sumRes] = await Promise.all([
          api.get('/api/cases'),
          api.get('/api/summary').catch(() => ({ data: null }))
        ]);

        if (isMounted) {
          // Take first 5 cases
          setRecentCases((casesRes.data || []).slice(0, 5));
          setSummaryData(sumRes.data);
        }
      } catch (err) {
        console.error('Failed to load dashboard supporting data', err);
      } finally {
        if (isMounted) {
          setCasesLoading(false);
        }
      }
    };

    fetchDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fadeIn select-none">
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="text-indigo-400" size={22} />
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">
              Investigation Command Center
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            System-wide operational oversight, automated analytical triage, and relational evidence graphs.
          </p>
        </div>

        {/* Global Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/cases/new')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 transition-all shadow-sm cursor-pointer"
            id="btn-register-case-dashboard"
          >
            <FolderPlus size={15} className="text-indigo-400" />
            <span>Register New Case</span>
          </button>
          <button
            onClick={() => navigate('/assistant')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-sm cursor-pointer"
          >
            <Bot size={15} />
            <span>Launch AI Assistant</span>
          </button>
        </div>
      </div>
      
      {/* 2. High-Level Summary Metrics Bar */}
      <DashboardOverview />

      {/* 3. Investigation Workflow Shortcuts */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <button
          onClick={() => navigate('/entities')}
          className="p-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-left transition-all group shadow-sm"
        >
          <div className="p-2 w-8 h-8 rounded-lg bg-sky-950 border border-sky-500/30 text-sky-400 flex items-center justify-center mb-2 group-hover:bg-sky-900 transition-colors">
            <Users size={16} />
          </div>
          <div className="text-xs font-bold text-slate-200">Search People</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Directory & Profiles</div>
        </button>

        <button
          onClick={() => navigate('/cases')}
          className="p-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-left transition-all group shadow-sm"
        >
          <div className="p-2 w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-500/30 text-indigo-400 flex items-center justify-center mb-2 group-hover:bg-indigo-900 transition-colors">
            <FolderOpen size={16} />
          </div>
          <div className="text-xs font-bold text-slate-200">Case Records</div>
          <div className="text-[10px] text-slate-400 mt-0.5">FIR investigations</div>
        </button>

        <button
          onClick={() => navigate('/search')}
          className="p-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-left transition-all group shadow-sm"
        >
          <div className="p-2 w-8 h-8 rounded-lg bg-emerald-950 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-2 group-hover:bg-emerald-900 transition-colors">
            <Search size={16} />
          </div>
          <div className="text-xs font-bold text-slate-200">Advanced Search</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Multi-field filters</div>
        </button>

        <button
          onClick={() => navigate('/network')}
          className="p-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-left transition-all group shadow-sm"
        >
          <div className="p-2 w-8 h-8 rounded-lg bg-purple-950 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-2 group-hover:bg-purple-900 transition-colors">
            <Network size={16} />
          </div>
          <div className="text-xs font-bold text-slate-200">Network Workspace</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Interactive graphs</div>
        </button>

        <button
          onClick={() => navigate('/analytics')}
          className="p-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-left transition-all group shadow-sm"
        >
          <div className="p-2 w-8 h-8 rounded-lg bg-amber-950 border border-amber-500/30 text-amber-400 flex items-center justify-center mb-2 group-hover:bg-amber-900 transition-colors">
            <BarChart3 size={16} />
          </div>
          <div className="text-xs font-bold text-slate-200">Graph Analytics</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Centrality & clusters</div>
        </button>

        <button
          onClick={() => navigate('/assistant')}
          className="p-3 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-left transition-all group shadow-sm"
        >
          <div className="p-2 w-8 h-8 rounded-lg bg-pink-950 border border-pink-500/30 text-pink-400 flex items-center justify-center mb-2 group-hover:bg-pink-900 transition-colors">
            <Bot size={16} />
          </div>
          <div className="text-xs font-bold text-slate-200">AI Assistant</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Natural language query</div>
        </button>
      </div>

      {/* 4. Core Workspaces: Left = Top Leads, Right = Recent Cases & Network Topology */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: Top Priority Leads (2 Cols wide) */}
        <div className="lg:col-span-2 space-y-6">
          <TopLeads />
        </div>

        {/* Right Column: Case Records & Network Overview (1 Col wide) */}
        <div className="space-y-6">
          {/* Key Case Records */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-4 py-3.5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderOpen size={15} className="text-indigo-400" />
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Important Case Records
                </h3>
              </div>
              <button
                onClick={() => navigate('/cases')}
                className="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <span>View All</span>
                <ChevronRight size={13} />
              </button>
            </div>

            <div className="divide-y divide-slate-800/80">
              {recentCases.map((c) => {
                const d = c.details || {};
                const title = d.title || d.case_title || c.id;
                const offence = d.offence_category || 'Investigation';
                const badgeStyle = OFFENCE_BADGES[offence] || 'text-slate-300 bg-slate-800 border-slate-700';

                return (
                  <div
                    key={c.id}
                    onClick={() => navigate(`/cases/${c.id}`)}
                    className="p-3.5 hover:bg-slate-850/50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="font-bold text-xs text-slate-200 hover:text-indigo-300 truncate">
                        {title}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border shrink-0 ${badgeStyle}`}>
                        {offence}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                      <span className="font-mono text-slate-400">{c.id} • {d.district || 'General'}</span>
                      <span className="font-mono text-[10px] text-slate-400 uppercase">{d.status || 'ACTIVE'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Compact Network Topology Summary */}
          {summaryData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Network size={15} className="text-indigo-400" />
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Network Topology Summary
                  </h3>
                </div>
                <button
                  onClick={() => navigate('/network')}
                  className="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <span>Explore Graph</span>
                  <ExternalLink size={12} />
                </button>
              </div>

              <div className="text-[11px] text-slate-400 leading-relaxed">
                The global intelligence graph spans <strong className="text-slate-200 font-mono">{summaryData.total_network_nodes}</strong> entities connected across <strong className="text-slate-200 font-mono">{summaryData.total_relationships}</strong> validated evidence edges.
              </div>

              {/* Entity Breakdown */}
              <div className="space-y-1.5 pt-1">
                {Object.entries(summaryData.node_counts_by_type || {}).slice(0, 5).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 last:border-0">
                    <span className="text-slate-400">{type}</span>
                    <span className="font-mono font-bold text-slate-200">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
