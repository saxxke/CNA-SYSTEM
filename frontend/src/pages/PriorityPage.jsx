import React, { useState, useEffect, useMemo } from 'react';
import { 
  AlertTriangle, Filter, Search, Loader2, AlertCircle, 
  ExternalLink, Network, Users, ArrowUpRight, ShieldAlert,
  ChevronRight, FileText
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import PriorityBadge from '../components/common/PriorityBadge';

export default function PriorityPage() {
  const navigate = useNavigate();

  const [leads, setLeads] = useState([]);
  const [personMap, setPersonMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedLevel, setSelectedLevel] = useState('ALL');
  const [selectedType, setSelectedType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    let isMounted = true;
    const fetchPriorityData = async () => {
      try {
        setLoading(true);
        const [prioRes, personsRes] = await Promise.all([
          api.get('/api/priority?limit=100'),
          api.get('/api/persons').catch(() => ({ data: [] }))
        ]);

        if (isMounted) {
          setLeads(prioRes.data || []);
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
          setError('Unable to load prioritized analytical leads from the API.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchPriorityData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filter leads
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      if (selectedLevel !== 'ALL' && lead.priority_level !== selectedLevel) return false;
      if (selectedType !== 'ALL' && lead.entity_type !== selectedType) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const id = (lead.entity_id || '').toLowerCase();
        const name = (personMap[lead.entity_id] || '').toLowerCase();
        const type = (lead.entity_type || '').toLowerCase();
        const reasons = (lead.reasons || []).join(' ').toLowerCase();

        if (!id.includes(q) && !name.includes(q) && !type.includes(q) && !reasons.includes(q)) {
          return false;
        }
      }

      return true;
    });
  }, [leads, selectedLevel, selectedType, searchQuery, personMap]);

  // Unique entity types present in leads
  const availableTypes = useMemo(() => {
    const types = new Set();
    leads.forEach((l) => {
      if (l.entity_type) types.add(l.entity_type);
    });
    return Array.from(types).sort();
  }, [leads]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={20} className="text-amber-400" />
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">
              Prioritized Analytical Leads
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Algorithmic priority triage based on cross-case centrality, diverse relational evidence, and structural bridging.
          </p>
        </div>

        {/* Safety Disclaimer */}
        <div className="text-[11px] text-amber-300/80 bg-amber-950/40 border border-amber-600/30 px-3 py-1.5 rounded-lg max-w-xs text-right">
          Investigation Priority • Does not determine guilt or criminality. Requires human verification.
        </div>
      </div>

      {/* 2. Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search leads by name, ID, or reason…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700/80 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Level:</span>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Levels</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Entity Types</option>
              {availableTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {(selectedLevel !== 'ALL' || selectedType !== 'ALL' || searchQuery) && (
            <button
              onClick={() => {
                setSelectedLevel('ALL');
                setSelectedType('ALL');
                setSearchQuery('');
              }}
              className="px-2.5 py-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* 3. Results Count */}
      <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
        <span>Displaying {filteredLeads.length} prioritized analytical leads</span>
      </div>

      {/* 4. Leads Cards */}
      {loading ? (
        <div className="p-16 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center justify-center space-y-3">
          <Loader2 size={32} className="animate-spin text-indigo-400" />
          <p className="text-xs font-semibold text-slate-300">Computing Priority Scorer Triage…</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-slate-900 border border-red-900/50 rounded-xl text-center space-y-2">
          <AlertCircle size={32} className="mx-auto text-red-400" />
          <h3 className="text-sm font-bold text-red-300">Priority Engine Error</h3>
          <p className="text-xs text-slate-400">{error}</p>
        </div>
      ) : filteredLeads.length === 0 ? (
        <div className="p-12 bg-slate-900 border border-slate-800 rounded-xl text-center space-y-2">
          <p className="text-sm font-semibold text-slate-300">No leads matched your filter criteria.</p>
          <p className="text-xs text-slate-400">Try loosening your search terms or filters.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLeads.map((lead, idx) => {
            const isPerson = lead.entity_type === 'PERSON';
            const resolvedName = isPerson ? personMap[lead.entity_id] || lead.entity_id : lead.entity_id;

            return (
              <div
                key={`${lead.entity_id}-${idx}`}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors shadow-sm space-y-4"
              >
                {/* Lead Top Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-slate-400">
                      #{idx + 1}
                    </span>
                    <div>
                      <div className="flex items-center gap-2.5">
                        <h3 className="text-base font-bold text-slate-100">
                          {resolvedName}
                        </h3>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                          {lead.entity_type}
                        </span>
                      </div>
                      {resolvedName !== lead.entity_id && (
                        <div className="font-mono text-[11px] text-slate-400 mt-0.5">
                          {lead.entity_id}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Priority Score</span>
                      <span className="text-base font-mono font-bold text-slate-100">
                        {Number(lead.priority_score).toFixed(4)}
                      </span>
                    </div>
                    <PriorityBadge level={lead.priority_level} />
                  </div>
                </div>

                {/* Reasons & Supporting Evidence Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {/* Triage Reasons */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                      Triage Reasons
                    </span>
                    <ul className="space-y-1">
                      {(lead.reasons || []).map((reason, rIdx) => (
                        <li key={rIdx} className="text-slate-300 text-xs flex items-start gap-1.5">
                          <span className="text-indigo-400 font-bold">•</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Supporting Evidence */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                      Supporting Corroboration
                    </span>
                    <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 space-y-1 text-slate-300 font-mono text-[11px]">
                      {(lead.supporting_evidence || []).map((ev, eIdx) => (
                        <p key={eIdx} className="leading-relaxed">
                          • {ev}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions Footer */}
                <div className="pt-3 border-t border-slate-800/60 flex items-center justify-end gap-2 text-xs">
                  {isPerson && (
                    <button
                      onClick={() => navigate(`/entities/${lead.entity_id}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-all"
                    >
                      <span>View Investigation Profile</span>
                      <ExternalLink size={12} />
                    </button>
                  )}
                  <button
                    onClick={() => navigate(`/network?case=${encodeURIComponent(lead.entity_id)}`)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
                  >
                    <Network size={13} />
                    <span>View in Network</span>
                  </button>
                  <button
                    onClick={() => navigate(`/search?q=${encodeURIComponent(lead.entity_id)}`)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
                  >
                    <Search size={13} />
                    <span>Cross-Search</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
