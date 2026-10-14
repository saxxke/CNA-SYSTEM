import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart3, Activity, GitCommit, Layers, Share2, 
  ExternalLink, Search, Loader2, AlertCircle, Info, 
  Users, FolderOpen, ArrowUpRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

const METRIC_TABS = [
  { id: 'degree', label: 'Degree Centrality', icon: GitCommit },
  { id: 'betweenness', label: 'Betweenness Centrality', icon: Share2 },
  { id: 'cross_case', label: 'Cross-Case Connectivity', icon: FolderOpen },
  { id: 'bridging', label: 'Community Bridging', icon: Layers },
  { id: 'diversity', label: 'Relationship Diversity', icon: Activity },
  { id: 'communities', label: 'Network Communities', icon: Users },
];

const METRIC_EXPLANATIONS = {
  degree: {
    title: 'Degree Centrality (Hub Identification)',
    description: 'Measures the proportion of direct connections an entity holds across the unweighted network graph. Entities with high degree centrality function as communication or operational hubs.',
    implication: 'High degree does not establish leadership or guilt; it highlights prominent relational focal points requiring investigator review.'
  },
  betweenness: {
    title: 'Betweenness Centrality (Information & Resource Bridges)',
    description: 'Measures how frequently an entity falls on the shortest analytical path between pairs of other nodes in the network.',
    implication: 'High betweenness indicates potential intermediaries, conduits, or couriers that broker interactions across distinct cells or sub-networks.'
  },
  cross_case: {
    title: 'Cross-Case Connectivity (Multi-FIR Links)',
    description: 'Identifies entities that appear in more than one distinct FIR case record across different police stations or timeframes.',
    implication: 'Entities linking multiple cases indicate serial associations, organized operational overlap, or recurring witnesses/associates.'
  },
  bridging: {
    title: 'Community Bridging (Cross-Cluster Connectors)',
    description: 'Measures entities that maintain direct connections to multiple algorithmic network communities or clusters.',
    implication: 'Critical for uncovering syndicate interfaces where otherwise isolated local groups share common logistical or financial conduits.'
  },
  diversity: {
    title: 'Relationship Diversity (Multi-Channel Activity)',
    description: 'Measures the distinct varieties of relationship types (calls, financial transactions, ownership, employment, physical presence) linked to an entity.',
    implication: 'High diversity indicates multifaceted interaction across both physical and digital/financial channels.'
  },
  communities: {
    title: 'Network Communities (Algorithmic Clustering)',
    description: 'Partitions the network into densely connected subgroups using modularity-based community detection.',
    implication: 'Provides an investigative lens into operational clusters, functional sub-cells, and co-accused groupings.'
  }
};

export default function AnalyticsPage() {
  const navigate = useNavigate();

  const [analytics, setAnalytics] = useState(null);
  const [personsMap, setPersonsMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState('degree');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    let isMounted = true;
    const fetchAnalyticsData = async () => {
      try {
        setLoading(true);
        const [analyticsRes, personsRes] = await Promise.all([
          api.get('/api/analytics'),
          api.get('/api/persons').catch(() => ({ data: [] }))
        ]);

        if (isMounted) {
          setAnalytics(analyticsRes.data);
          const pMap = {};
          (personsRes.data || []).forEach((p) => {
            if (p.person_id) {
              pMap[p.person_id] = p.full_name || p.primary_alias || p.person_id;
            }
          });
          setPersonsMap(pMap);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError('Unable to load graph analytics from the intelligence pipeline.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchAnalyticsData();
    return () => {
      isMounted = false;
    };
  }, []);

  const explanation = METRIC_EXPLANATIONS[activeTab];

  // Filter items for current tab
  const filteredList = useMemo(() => {
    if (!analytics) return [];
    const q = searchQuery.toLowerCase().trim();

    let list = [];
    if (activeTab === 'degree') {
      list = analytics.degree_centrality || [];
    } else if (activeTab === 'betweenness') {
      list = analytics.betweenness_centrality || [];
    } else if (activeTab === 'cross_case') {
      list = analytics.cross_case_connectivity || [];
    } else if (activeTab === 'bridging') {
      list = analytics.community_bridging || [];
    } else if (activeTab === 'diversity') {
      list = analytics.relationship_diversity || [];
    } else if (activeTab === 'communities') {
      list = analytics.communities || [];
    }

    if (!q) return list;

    return list.filter((item) => {
      const id = (item.entity_id || `Community ${item.community_id}` || '').toLowerCase();
      const name = (personsMap[item.entity_id] || '').toLowerCase();
      const type = (item.entity_type || '').toLowerCase();
      return id.includes(q) || name.includes(q) || type.includes(q);
    });
  }, [analytics, activeTab, searchQuery, personsMap]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 size={20} className="text-indigo-400" />
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">
              Graph Intelligence & Network Analytics
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Topological analysis computed via NetworkX algorithms. Identifies structural hubs, bridges, and multi-case links.
          </p>
        </div>

        {/* Global Safety Notice */}
        <div className="text-[11px] text-amber-300/80 bg-amber-950/40 border border-amber-600/30 px-3 py-1.5 rounded-lg max-w-xs text-right">
          Topological scores are analytical leads. Human verification required.
        </div>
      </div>

      {/* 2. Metric Tabs Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/80">
        {METRIC_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setSearchQuery('');
              }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all shrink-0 ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 3. Metric Context & Investigative Explanation Card */}
      {explanation && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                {explanation.title}
              </h3>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {explanation.description}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 shrink-0">
              <Info size={16} />
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800/60 text-[11px] text-amber-300/80 font-medium">
            <strong>Investigative Caution:</strong> {explanation.implication}
          </div>
        </div>
      )}

      {/* 4. Table Controls (Search & Result Count) */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-72">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search within this metric…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <span className="text-xs text-slate-400 font-mono">
          Showing {filteredList.length} ranked entries
        </span>
      </div>

      {/* 5. Analytics Data View */}
      {loading ? (
        <div className="p-16 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center justify-center space-y-3">
          <Loader2 size={32} className="animate-spin text-indigo-400" />
          <p className="text-xs font-semibold text-slate-300">Evaluating Network Topology…</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-slate-900 border border-red-900/50 rounded-xl text-center space-y-2">
          <AlertCircle size={32} className="mx-auto text-red-400" />
          <h3 className="text-sm font-bold text-red-300">Analytics Engine Error</h3>
          <p className="text-xs text-slate-400">{error}</p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          {activeTab === 'communities' ? (
            /* Communities View */
            <div className="divide-y divide-slate-800/80">
              {filteredList.map((comm) => (
                <div key={comm.community_id} className="p-4 hover:bg-slate-850/40 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm text-slate-100">
                      Community Cluster #{comm.community_id}
                    </span>
                    <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {comm.size || comm.entities?.length || 0} Members
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {(comm.entities || []).map((entId) => {
                      const isPerson = entId.startsWith('PERSON');
                      const name = personsMap[entId] || entId;
                      return (
                        <button
                          key={entId}
                          onClick={() => {
                            if (isPerson) navigate(`/entities/${entId}`);
                            else navigate(`/search?q=${encodeURIComponent(entId)}`);
                          }}
                          className="px-2 py-1 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[11px] font-mono text-slate-300 hover:text-indigo-300 transition-colors"
                        >
                          {name !== entId ? `${name} (${entId})` : entId}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Standard Centrality / Diversity / Bridging Table */
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Rank</th>
                    <th className="px-4 py-3">Entity Name & Identifier</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">
                      {activeTab === 'degree' ? 'Degree Centrality' :
                       activeTab === 'betweenness' ? 'Betweenness Score' :
                       activeTab === 'cross_case' ? 'Connected Cases' :
                       activeTab === 'bridging' ? 'Bridged Communities' :
                       'Diversity Score'}
                    </th>
                    <th className="px-4 py-3">Topological Details</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {filteredList.slice(0, 50).map((row, idx) => {
                    const isPerson = row.entity_type === 'PERSON';
                    const name = isPerson ? personsMap[row.entity_id] || row.entity_id : row.entity_id;

                    return (
                      <tr key={row.entity_id} className="hover:bg-slate-850/40 transition-colors">
                        <td className="px-4 py-3 font-mono font-bold text-slate-400">
                          #{idx + 1}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-bold text-slate-100">{name}</div>
                          {name !== row.entity_id && (
                            <div className="font-mono text-[10px] text-slate-400">{row.entity_id}</div>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                            {row.entity_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-slate-100">
                          {activeTab === 'degree' && Number(row.centrality_score).toFixed(4)}
                          {activeTab === 'betweenness' && Number(row.betweenness_score).toFixed(4)}
                          {activeTab === 'cross_case' && `${row.case_count || row.connected_cases?.length || 0} Cases`}
                          {activeTab === 'bridging' && `${row.community_count || row.bridged_communities?.length || 0} Communities`}
                          {activeTab === 'diversity' && `${row.diversity_score} Channel Types`}
                        </td>
                        <td className="px-4 py-3 text-slate-400 max-w-xs truncate">
                          {activeTab === 'cross_case' && (row.connected_cases || []).join(', ')}
                          {activeTab === 'bridging' && `Communities: ${(row.bridged_communities || []).join(', ')}`}
                          {activeTab === 'diversity' && (row.relationship_types || []).join(', ')}
                          {(activeTab === 'degree' || activeTab === 'betweenness') && 'Normalized graph fraction'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {isPerson ? (
                            <button
                              onClick={() => navigate(`/entities/${row.entity_id}`)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 font-semibold"
                            >
                              <span>Profile</span>
                              <ArrowUpRight size={12} />
                            </button>
                          ) : (
                            <button
                              onClick={() => navigate(`/search?q=${encodeURIComponent(row.entity_id)}`)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold"
                            >
                              <span>Search</span>
                              <Search size={11} />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
