import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  FolderOpen, Database, HeartHandshake, Network, Target, 
  AlertCircle, ArrowLeft, Loader2, Shield, Info, ShieldAlert
} from 'lucide-react';
import api from '../api/client';
import PersonHeader from '../components/entities/PersonHeader';
import PersonCasesTable from '../components/entities/PersonCasesTable';
import PersonAssets from '../components/entities/PersonAssets';
import PersonFamilyPreview from '../components/entities/PersonFamilyPreview';
import PersonNetworkSummary from '../components/entities/PersonNetworkSummary';
import PersonEvidenceRelationships from '../components/entities/PersonEvidenceRelationships';
import PersonPriorityAnalytics from '../components/entities/PersonPriorityAnalytics';

export default function PersonProfilePage() {
  const { entityId } = useParams();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active tab state
  const [activeTab, setActiveTab] = useState('cases'); // 'cases' | 'network' | 'assets' | 'analytics' | 'family'

  useEffect(() => {
    if (!entityId) return;

    let isMounted = true;
    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get(`/api/entities/${entityId}`);
        if (isMounted) {
          setProfile(res.data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Person record not found in synthetic database.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchProfile();
    return () => {
      isMounted = false;
    };
  }, [entityId]);

  if (loading) {
    return (
      <div className="p-16 max-w-7xl mx-auto flex flex-col items-center justify-center space-y-4">
        <Loader2 size={36} className="animate-spin text-indigo-400" />
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-200">Compiling Person Investigation Profile</p>
          <p className="text-xs text-slate-400 mt-0.5">Fetching records, associated cases, assets, and linkages for {entityId}…</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="p-8 max-w-2xl mx-auto mt-12 bg-slate-900 rounded-xl border border-red-900/50 shadow-sm text-center space-y-4">
        <AlertCircle size={36} className="mx-auto text-red-400" />
        <div>
          <h2 className="text-base font-bold text-slate-100">Entity Record Unavailable</h2>
          <p className="text-xs text-slate-400 mt-1">{error || 'No matching person record found.'}</p>
        </div>
        <button
          onClick={() => navigate('/entities')}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Return to Entity Explorer</span>
        </button>
      </div>
    );
  }

  const cases = profile.associated_cases || [];
  const assets = profile.assets || {};
  const family = profile.family_relationships || [];
  const relationships = profile.evidence_relationships || [];
  const networkSummary = profile.network_summary || {};
  const priority = profile.priority_information;
  const graphMetrics = profile.graph_metrics || {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fadeIn select-none">
      {/* 1. PERSON HEADER */}
      <PersonHeader
        profile={profile}
        onBack={() => navigate('/entities')}
      />

      {/* 2. TABBED DOSSIER SECTIONS */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-4 overflow-x-auto">
          <button
            onClick={() => setActiveTab('cases')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'cases'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FolderOpen size={14} />
            <span>Associated Case Records</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold">
              {cases.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('network')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'network'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network size={14} />
            <span>Relational Evidence</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300 font-bold">
              {relationships.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('assets')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'assets'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database size={14} />
            <span>Assets & Accounts</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300 font-bold">
              {assets.total_assets_count ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'analytics'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Target size={14} />
            <span>Investigation Priority</span>
            {priority && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-950 text-amber-300 border border-amber-800 font-bold">
                {priority.priority_level || 'LEAD'}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('family')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'family'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <HeartHandshake size={14} />
            <span>Family Directory (Civilian Isolation)</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
              {family.length}
            </span>
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-6">
          {activeTab === 'cases' && (
            <PersonCasesTable cases={cases} />
          )}

          {activeTab === 'network' && (
            <div className="space-y-8">
              <PersonNetworkSummary
                summary={networkSummary}
                personId={entityId}
                fullName={profile.demographics?.full_name}
              />
              <div className="pt-4 border-t border-slate-800">
                <PersonEvidenceRelationships
                  relationships={relationships}
                  personId={entityId}
                />
              </div>
            </div>
          )}

          {activeTab === 'assets' && (
            <PersonAssets assets={assets} />
          )}

          {activeTab === 'analytics' && (
            <PersonPriorityAnalytics
              priority={priority}
              graphMetrics={graphMetrics}
            />
          )}

          {activeTab === 'family' && (
            <div className="space-y-4">
              {/* Mandatory Isolation Notice */}
              <div className="p-3 bg-amber-950/40 border border-amber-500/30 rounded-lg text-xs text-amber-300 flex items-start gap-2">
                <ShieldAlert size={16} className="shrink-0 mt-0.5 text-amber-400" />
                <div>
                  <span className="font-bold block">Civilian Privacy & Isolation Boundary</span>
                  Family relationships do not imply case involvement, criminality, or investigative relevance.
                  Family ties are strictly excluded from network graph edges and algorithmic priority scoring.
                </div>
              </div>

              <PersonFamilyPreview
                family={family}
                subjectName={profile.demographics?.full_name || 'Subject'}
                subjectId={entityId}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
