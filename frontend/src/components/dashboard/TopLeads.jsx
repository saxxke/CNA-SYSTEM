import React, { useState, useEffect } from 'react';
import { Loader2, AlertCircle, ExternalLink, Network, ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import PriorityBadge from '../common/PriorityBadge';

export default function TopLeads() {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [personMap, setPersonMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchLeads = async () => {
      try {
        setLoading(true);
        const [prioRes, personsRes] = await Promise.all([
          api.get('/api/priority?limit=5'),
          api.get('/api/persons').catch(() => ({ data: [] }))
        ]);

        if (isMounted) {
          setLeads(prioRes.data || []);
          
          // Map person_id -> full_name
          const pMap = {};
          (personsRes.data || []).forEach((p) => {
            if (p.person_id) {
              pMap[p.person_id] = p.full_name || p.primary_alias || p.person_id;
            }
          });
          setPersonMap(pMap);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to connect to priority intelligence API');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    fetchLeads();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 flex flex-col items-center justify-center min-h-[280px]">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-400 mb-3" />
        <p className="text-xs font-semibold text-slate-400">Computing Algorithmic Priority Triage…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border border-red-900/50 rounded-xl p-8 flex flex-col items-center justify-center min-h-[280px]">
        <AlertCircle className="w-10 h-10 text-red-400 mb-3" />
        <p className="text-sm font-bold text-red-300">Priority Engine Unavailable</p>
        <p className="text-xs text-slate-400 mt-1">{error}</p>
      </div>
    );
  }

  if (!leads || leads.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center min-h-[200px] flex flex-col items-center justify-center">
        <p className="text-sm text-slate-400">No prioritized analytical leads currently flagged.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm select-none">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Top Priority Analytical Leads</h3>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Algorithmic triage based on network centrality and evidence corroboration. Requires human verification.
          </p>
        </div>
        <button
          onClick={() => navigate('/priority')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-indigo-400 hover:text-indigo-300 hover:bg-indigo-950/40 border border-indigo-500/30 transition-all"
        >
          <span>All Priority Leads</span>
          <ArrowRight size={13} />
        </button>
      </div>
      
      {/* Leads List */}
      <div className="divide-y divide-slate-800/80">
        {leads.map((lead, idx) => {
          const isPerson = lead.entity_type === 'PERSON';
          const resolvedName = isPerson ? personMap[lead.entity_id] || lead.entity_id : lead.entity_id;

          return (
            <div key={idx} className="p-5 hover:bg-slate-850/40 transition-colors">
              {/* Lead Top Bar */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h4 className="text-base font-bold text-slate-100">
                      {resolvedName}
                    </h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                      {lead.entity_type}
                    </span>
                    {resolvedName !== lead.entity_id && (
                      <span className="text-[11px] font-mono text-slate-400">
                        {lead.entity_id}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Score</span>
                    <span className="text-sm font-mono font-bold text-slate-200">
                      {Number(lead.priority_score).toFixed(3)}
                    </span>
                  </div>
                  <PriorityBadge level={lead.priority_level} />
                </div>
              </div>
              
              {/* Reasons & Evidence Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Reasons */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Triage Reasoning
                  </span>
                  <ul className="space-y-1">
                    {(lead.reasons || []).map((reason, i) => (
                      <li key={i} className="text-slate-300 text-xs flex items-start gap-1.5">
                        <span className="text-indigo-400 font-bold">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Supporting Evidence */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Supporting Relational Evidence
                  </span>
                  <div className="bg-slate-950/80 rounded-lg p-2.5 border border-slate-800/80 space-y-1 text-slate-300">
                    {(lead.supporting_evidence || []).slice(0, 2).map((evidence, i) => (
                      <p key={i} className="text-[11px] font-mono line-clamp-2 text-slate-300">
                        • {evidence}
                      </p>
                    ))}
                    {(lead.supporting_evidence || []).length > 2 && (
                      <p className="text-[10px] text-indigo-400 font-semibold pt-0.5">
                        + {(lead.supporting_evidence.length - 2)} additional corroborating evidence links
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-end gap-2">
                {isPerson && (
                  <button
                    onClick={() => navigate(`/entities/${lead.entity_id}`)}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-all"
                  >
                    <span>Inspect Investigation Profile</span>
                    <ExternalLink size={12} />
                  </button>
                )}
                <button
                  onClick={() => navigate(`/search?q=${encodeURIComponent(lead.entity_id)}`)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  <span>Search Cross-References</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
