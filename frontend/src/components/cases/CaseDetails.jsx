import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, Network, Users, Database, Link2, Share2, 
  MapPin, Shield, Calendar, FileText, AlertCircle, Phone, 
  CreditCard, Car, Building2, ExternalLink, CheckCircle, 
  Clock, Hash, ShieldAlert, ChevronRight, UserCheck, Loader2
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import PersonPreviewModal from './PersonPreviewModal';

const OFFENCE_COLORS = {
  'Cyber Crime': 'bg-purple-950/80 text-purple-300 border-purple-500/40',
  'Extortion': 'bg-rose-950/80 text-rose-300 border-rose-500/40',
  'Kidnapping': 'bg-amber-950/80 text-amber-300 border-amber-500/40',
  'Financial Fraud': 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
  'Narcotics': 'bg-red-950/80 text-red-300 border-red-500/40',
  'Theft': 'bg-blue-950/80 text-blue-300 border-blue-500/40',
  'Homicide': 'bg-stone-900 text-stone-300 border-stone-600',
  'Smuggling': 'bg-indigo-950/80 text-indigo-300 border-indigo-500/40',
};

export default function CaseDetails({ caseId, onBack, onSelectCase }) {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active Tab: 'persons' | 'entities' | 'relationships' | 'related_cases'
  const [activeTab, setActiveTab] = useState('persons');

  // Person Modal
  const [selectedPerson, setSelectedPerson] = useState(null);

  useEffect(() => {
    if (!caseId) return;

    let isMounted = true;
    const fetchCaseDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get(`/api/cases/${caseId}`);
        if (isMounted) {
          setData(res.data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Failed to load case intelligence details.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchCaseDetails();
    return () => {
      isMounted = false;
    };
  }, [caseId]);

  if (loading) {
    return (
      <div className="p-16 bg-slate-900 rounded-xl border border-slate-800 flex flex-col items-center justify-center space-y-4">
        <Loader2 size={36} className="animate-spin text-indigo-400" />
        <div className="text-center">
          <p className="text-sm font-bold text-slate-100">Loading Case Intelligence Dossier</p>
          <p className="text-xs text-slate-400 mt-1">Fetching associated entities, relationships, and cross-case leads for {caseId}…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    const isForbidden = error && (
      error.toLowerCase().includes('restricted') ||
      error.toLowerCase().includes('need-to-know') ||
      error.toLowerCase().includes('jurisdiction') ||
      error.toLowerCase().includes('assigned') ||
      error.toLowerCase().includes('unassigned')
    );

    return (
      <div className={`p-10 bg-slate-900 rounded-xl border ${isForbidden ? 'border-amber-700/60 bg-slate-900/95' : 'border-red-900/50'} text-center space-y-4 max-w-2xl mx-auto my-8 shadow-2xl`}>
        {isForbidden ? (
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
            <ShieldAlert size={36} />
          </div>
        ) : (
          <AlertCircle size={36} className="mx-auto text-red-400" />
        )}
        
        <div className="space-y-2">
          <h3 className="text-lg font-bold text-slate-100">
            {isForbidden ? 'Access Restricted: Need-to-Know Authorization Required' : 'Unable to Load Case Details'}
          </h3>
          <p className="text-xs text-slate-300 font-mono bg-slate-950/80 p-3 rounded-lg border border-slate-800 leading-relaxed text-left">
            {error || 'Case record not found in system or access could not be authorized.'}
          </p>
          {isForbidden && (
            <p className="text-[11px] text-slate-400">
              Pursuant to investigation security protocols, full case dossiers, suspect rosters, and evidence graphs are restricted exclusively to actively assigned Investigating Officers and state supervisory authorities.
            </p>
          )}
        </div>

        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg cursor-pointer"
        >
          <ArrowLeft size={14} /> Return to Case Explorer
        </button>
      </div>
    );
  }

  const details = data.details || {};
  const associatedPersons = data.associated_persons || [];
  const relatedEntities = data.related_entities || { locations: [], phones: [], bank_accounts: [], vehicles: [], organizations: [] };
  const relationships = data.relationships || [];
  const relatedCases = data.related_cases || [];

  const offenceCategory = details.offence_category || 'General Enquiry';
  const offenceBadgeClass = OFFENCE_COLORS[offenceCategory] || 'bg-slate-800 text-slate-300 border-slate-700';
  const isClosed = (details.status || '').toUpperCase() === 'CLOSED';

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-indigo-400 transition-colors self-start"
        >
          <ArrowLeft size={15} />
          <span>Back to Case Explorer</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 font-mono">
            {caseId}
          </span>
          <button
            onClick={() => navigate(`/network?caseId=${caseId}`)}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-sm transition-all"
            title="Open case in interactive cytoscape network graph"
          >
            <Network size={14} />
            <span>Open Case Network</span>
          </button>
        </div>
      </div>

      {/* Case Header Card */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-bold text-indigo-300 bg-indigo-950 border border-indigo-800 px-2.5 py-0.5 rounded">
                {caseId}
              </span>
              <span className="font-mono text-xs text-slate-300 bg-slate-800 px-2.5 py-0.5 rounded">
                {details.fir_number || 'FIR Unassigned'}
              </span>
              <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full border ${offenceBadgeClass}`}>
                {offenceCategory}
              </span>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                isClosed 
                  ? 'bg-slate-800 text-slate-400 border-slate-700' 
                  : 'bg-emerald-950 text-emerald-300 border-emerald-800'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${isClosed ? 'bg-slate-400' : 'bg-emerald-400'}`} />
                {details.status || 'OPEN'}
              </span>
            </div>

            <h1 className="text-xl md:text-2xl font-bold text-slate-100 leading-snug">
              {details.title || details.case_title || `Case Dossier ${caseId}`}
            </h1>

            <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar size={13} className="text-slate-500" />
                Opened: {details.date_opened || 'Unknown'}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-mono">
                <FileText size={13} className="text-slate-500" />
                Legal Section: {details.legal_section || 'N/A'}
              </span>
            </div>
          </div>

          {/* Quick Metrics Pills */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 gap-2 shrink-0">
            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center min-w-[110px]">
              <div className="text-lg font-mono font-bold text-slate-100">{associatedPersons.length}</div>
              <div className="text-[10px] text-slate-400 uppercase font-bold">Associated People</div>
            </div>
            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center min-w-[110px]">
              <div className="text-lg font-mono font-bold text-slate-100">{relatedEntities.total_count ?? 0}</div>
              <div className="text-[10px] text-slate-400 uppercase font-bold">Related Entities</div>
            </div>
            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center min-w-[110px]">
              <div className="text-lg font-mono font-bold text-indigo-400">{relationships.length}</div>
              <div className="text-[10px] text-slate-400 uppercase font-bold">Evidence Edges</div>
            </div>
            <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center min-w-[110px]">
              <div className="text-lg font-mono font-bold text-amber-400">{relatedCases.length}</div>
              <div className="text-[10px] text-slate-400 uppercase font-bold">Linked Cases</div>
            </div>
          </div>
        </div>

        {/* Description & Jurisdiction Card */}
        <div className="pt-4 border-t border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-1.5">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Case Narrative & Background
            </div>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/80 p-3 rounded-lg border border-slate-800">
              {details.description || 'No detailed case narrative recorded for this synthetic entry.'}
            </p>
          </div>

          <div className="space-y-2 bg-slate-950/80 p-3 rounded-lg border border-slate-800 text-xs">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Jurisdiction</div>
            <div className="space-y-1 text-slate-300">
              <div className="flex items-start gap-1.5">
                <MapPin size={13} className="text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="font-semibold text-slate-200">{details.district || 'Headquarters'}</span>
                  {details.state ? `, ${details.state}` : ''}
                </div>
              </div>
              <div className="text-slate-400 pl-5">
                PS: {details.police_station || 'Central PS'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Structured Investigation Tabs */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-4 overflow-x-auto">
          <button
            onClick={() => setActiveTab('persons')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'persons'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users size={14} />
            <span>Associated People</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 font-bold">
              {associatedPersons.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('entities')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'entities'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database size={14} />
            <span>Related Entities</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300 font-bold">
              {relatedEntities.total_count ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('relationships')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'relationships'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Link2 size={14} />
            <span>Evidence Relationships</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300 font-bold">
              {relationships.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('related_cases')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
              activeTab === 'related_cases'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Share2 size={14} />
            <span>Cross-Case Leads</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-950 text-amber-300 border border-amber-800 font-bold">
              {relatedCases.length}
            </span>
          </button>
        </div>

        {/* Tab Content Panels */}
        <div className="p-6">
          {/* TAB 1: Associated Persons */}
          {activeTab === 'persons' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <p>
                  Individuals connected with this case record. Click <strong>Inspect Profile</strong> to review full dossier.
                </p>
                <span className="text-[11px] text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-500/40">
                  Analytical Lead Only
                </span>
              </div>

              {associatedPersons.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  No individual person records directly linked to this case.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {associatedPersons.map((person) => (
                    <div
                      key={person.person_id}
                      className="border border-slate-800 rounded-xl p-4 bg-slate-950/80 hover:border-slate-700 transition-all flex flex-col justify-between space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-sky-400 text-sm">
                            {person.full_name ? person.full_name.charAt(0).toUpperCase() : 'P'}
                          </div>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-bold text-slate-100 text-sm">{person.full_name}</span>
                              <span className="font-mono text-[10px] text-slate-400 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                                {person.person_id}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5">
                              {person.primary_alias ? `Alias: "${person.primary_alias}"` : 'No registered alias'}
                            </div>
                          </div>
                        </div>

                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                          {person.role || 'ASSOCIATE'}
                        </span>
                      </div>

                      {/* Association Narrative */}
                      <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 text-xs text-slate-300 italic">
                        "{person.association_type || 'Associated with registered case record.'}"
                      </div>

                      {/* Details Row */}
                      <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 pt-1">
                        <div>
                          <span>Demographics:</span>{' '}
                          <span className="text-slate-200 font-medium">
                            {person.gender || 'N/A'}, {person.age ? `${person.age}y` : ''}
                          </span>
                        </div>
                        <div>
                          <span>Occupation:</span>{' '}
                          <span className="text-slate-200 font-medium truncate inline-block max-w-[130px] align-bottom">
                            {person.occupation || 'Unspecified'}
                          </span>
                        </div>
                        <div>
                          <span>Location:</span>{' '}
                          <span className="text-slate-200 font-medium">
                            {person.district || person.city || 'Regional Area'}
                          </span>
                        </div>
                        <div>
                          <span>Linked Cases:</span>{' '}
                          <span className="text-indigo-400 font-semibold">
                            {person.linked_cases_count ?? 1} case(s)
                          </span>
                        </div>
                      </div>

                      {/* Card Action */}
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400">
                          Analytical identity record
                        </span>
                        <button
                          onClick={() => navigate(`/entities/${person.person_id}`)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 transition-colors"
                        >
                          <UserCheck size={13} />
                          <span>Inspect Profile</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Related Entities */}
          {activeTab === 'entities' && (
            <div className="space-y-6">
              {/* Primary Location */}
              {relatedEntities.locations && relatedEntities.locations.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <MapPin size={13} className="text-indigo-400" />
                    Case Location Registry
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {relatedEntities.locations.map((loc) => (
                      <div key={loc.entity_id} className="p-3.5 border border-slate-800 rounded-lg bg-slate-950/80 flex items-start gap-3">
                        <div className="p-2 bg-indigo-950 text-indigo-400 rounded-lg shrink-0 border border-indigo-800">
                          <MapPin size={15} />
                        </div>
                        <div className="text-xs space-y-0.5">
                          <div className="font-bold text-slate-100">{loc.name}</div>
                          <div className="text-slate-400 font-mono text-[11px]">{loc.entity_id} • {loc.location_type}</div>
                          <div className="text-slate-300">
                            {loc.city && `${loc.city}, `}{loc.district}, {loc.state} {loc.pin_code && `— PIN: ${loc.pin_code}`}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Registered Phones */}
              {relatedEntities.phones && relatedEntities.phones.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Phone size={13} className="text-emerald-400" />
                    Registered Telecom Identifiers ({relatedEntities.phones.length})
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {relatedEntities.phones.map((ph, idx) => (
                      <div key={`${ph.entity_id}-${idx}`} className="p-3 border border-slate-800 rounded-lg bg-slate-950/80 flex items-center gap-3">
                        <div className="p-2 bg-emerald-950 text-emerald-400 rounded-lg shrink-0 border border-emerald-800">
                          <Phone size={14} />
                        </div>
                        <div className="text-xs overflow-hidden">
                          <div className="font-mono font-bold text-slate-100">{ph.number}</div>
                          <div className="text-[11px] text-slate-400 truncate">
                            Linked: {ph.associated_person_name || ph.associated_person_id || 'Case Lead'}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            {ph.entity_id} • {ph.phone_type}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Bank Accounts */}
              {relatedEntities.bank_accounts && relatedEntities.bank_accounts.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <CreditCard size={13} className="text-amber-400" />
                    Financial Instruments & Accounts ({relatedEntities.bank_accounts.length})
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {relatedEntities.bank_accounts.map((ba, idx) => (
                      <div key={`${ba.entity_id}-${idx}`} className="p-3 border border-slate-800 rounded-lg bg-slate-950/80 flex items-center gap-3">
                        <div className="p-2 bg-amber-950 text-amber-400 rounded-lg shrink-0 border border-amber-800">
                          <CreditCard size={14} />
                        </div>
                        <div className="text-xs overflow-hidden">
                          <div className="font-mono font-bold text-slate-100 truncate">
                            •••• {ba.account_number.slice(-4) || ba.account_number}
                          </div>
                          <div className="text-[11px] text-slate-300 truncate">{ba.bank_name}</div>
                          <div className="text-[10px] text-slate-400 truncate">
                            Holder: {ba.associated_person_name || ba.associated_person_id}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Vehicles */}
              {relatedEntities.vehicles && relatedEntities.vehicles.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Car size={13} className="text-purple-400" />
                    Vehicles Registered to Leads ({relatedEntities.vehicles.length})
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {relatedEntities.vehicles.map((vh, idx) => (
                      <div key={`${vh.entity_id}-${idx}`} className="p-3 border border-slate-800 rounded-lg bg-slate-950/80 flex items-center gap-3">
                        <div className="p-2 bg-purple-950 text-purple-400 rounded-lg shrink-0 border border-purple-800">
                          <Car size={14} />
                        </div>
                        <div className="text-xs overflow-hidden">
                          <div className="font-mono font-bold text-slate-100">{vh.registration_number}</div>
                          <div className="text-[11px] text-slate-300">{vh.color} {vh.model} ({vh.vehicle_type})</div>
                          <div className="text-[10px] text-slate-400 truncate">Owner: {vh.associated_person_name}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Evidence Relationships */}
          {activeTab === 'relationships' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <p>
                  Evidence-backed relationships detected via telecom analysis, financial records, and graph extraction.
                </p>
                <button
                  onClick={() => navigate(`/network?caseId=${caseId}`)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1"
                >
                  <Network size={13} /> Open Visual Network
                </button>
              </div>

              {relationships.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  No cross-entity relationships indexed for this case record.
                </div>
              ) : (
                <div className="overflow-x-auto border border-slate-800 rounded-lg bg-slate-950/80">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                        <th className="py-2.5 px-3">Source Lead</th>
                        <th className="py-2.5 px-3">Relationship Type</th>
                        <th className="py-2.5 px-3">Target Lead</th>
                        <th className="py-2.5 px-3">Confidence</th>
                        <th className="py-2.5 px-3">Evidence Snippet</th>
                        <th className="py-2.5 px-3">Method</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {relationships.map((rel, idx) => (
                        <tr key={rel.relationship_id || idx} className="hover:bg-slate-900/50 transition-colors">
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <div className="font-bold text-slate-100">{rel.source_label}</div>
                            <div className="text-[10px] text-slate-400 font-mono">{rel.source_id}</div>
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                              {rel.relationship_type}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <div className="font-bold text-slate-100">{rel.target_label}</div>
                            <div className="text-[10px] text-slate-400 font-mono">{rel.target_id}</div>
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <span className="font-mono font-bold text-slate-100">
                              {Math.round((rel.confidence || 0) * 100)}%
                            </span>
                          </td>
                          <td className="py-2.5 px-3 max-w-xs">
                            <p className="text-[11px] font-mono text-slate-300 truncate" title={rel.evidence}>
                              "{rel.evidence}"
                            </p>
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap text-[10px] font-mono text-slate-400">
                            {rel.detection_method}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: Related Cases */}
          {activeTab === 'related_cases' && (
            <div className="space-y-4">
              <div className="text-xs text-slate-400">
                Cross-case network intelligence: other cases sharing associated person leads, assets, or network connections.
              </div>

              {relatedCases.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  No cross-case linkages detected for this case. This case is currently isolated in the registry.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {relatedCases.map((rc) => (
                    <div
                      key={rc.case_id}
                      className="border border-slate-800 rounded-xl p-4 bg-slate-950/80 hover:border-slate-700 transition-all flex flex-col justify-between space-y-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-xs text-indigo-300 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
                              {rc.case_id}
                            </span>
                            <span className="text-xs font-semibold text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                              {rc.offence_category}
                            </span>
                          </div>
                          <h4 className="font-bold text-slate-100 text-sm mt-1.5 line-clamp-1">
                            {rc.title}
                          </h4>
                          <p className="text-xs text-slate-400 mt-0.5">{rc.district || 'State Area'}</p>
                        </div>

                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-950 text-amber-300 border border-amber-800">
                          {rc.link_strength === 'HIGH' ? 'Multi-Link' : 'Network Lead'}
                        </span>
                      </div>

                      <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-xs text-slate-300">
                        <div className="font-bold text-slate-400 text-[10px] uppercase mb-0.5">Linkage Reason:</div>
                        <div>{rc.reason}</div>
                      </div>

                      <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400">
                          Cross-Case Connection
                        </span>
                        <button
                          onClick={() => onSelectCase(rc.case_id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 transition-colors"
                        >
                          <span>Switch to Case</span>
                          <ChevronRight size={13} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Person Preview Modal */}
      {selectedPerson && (
        <PersonPreviewModal
          person={selectedPerson}
          onClose={() => setSelectedPerson(null)}
          onSelectCase={(cid) => {
            setSelectedPerson(null);
            onSelectCase(cid);
          }}
        />
      )}
    </div>
  );
}
