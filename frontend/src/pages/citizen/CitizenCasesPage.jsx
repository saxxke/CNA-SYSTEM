import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../../api/client';
import { 
  FolderOpen, Calendar, Building, MapPin, Shield, 
  Info, Loader2, AlertCircle, FileText, CheckCircle2, ChevronRight, X
} from 'lucide-react';

export default function CitizenCasesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedCaseParam = searchParams.get('caseId');

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedCase, setSelectedCase] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // Load citizen authorized cases list
  useEffect(() => {
    async function loadCases() {
      try {
        setLoading(true);
        setError(null);
        // Strictly calls citizen-safe endpoint
        const res = await api.get('/api/citizen/cases');
        setCases(res.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load authorized citizen cases.');
      } finally {
        setLoading(false);
      }
    }
    loadCases();
  }, []);

  // If a case is selected in URL or state, fetch sanitized detail via /api/citizen/cases/{case_id}
  useEffect(() => {
    if (!selectedCaseParam) {
      setSelectedCase(null);
      return;
    }

    async function loadCaseDetail() {
      try {
        setDetailLoading(true);
        setDetailError(null);
        const res = await api.get(`/api/citizen/cases/${selectedCaseParam}`);
        setSelectedCase(res.data);
      } catch (err) {
        setDetailError(err.response?.data?.detail || 'Unable to retrieve case status for this record.');
        setSelectedCase(null);
      } finally {
        setDetailLoading(false);
      }
    }

    loadCaseDetail();
  }, [selectedCaseParam]);

  const handleSelectCase = (caseId) => {
    setSearchParams({ caseId });
  };

  const handleClearSelection = () => {
    setSearchParams({});
    setSelectedCase(null);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <FolderOpen className="text-teal-400" size={20} />
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              My Registered Cases
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Official case status records explicitly authorized for your verified citizen profile.
          </p>
        </div>

        <div className="px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-mono flex items-center gap-2 self-start sm:self-auto">
          <Shield size={13} />
          <span>Object-Level Authorization Enforced</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 size={26} className="animate-spin text-teal-400" />
          <span className="text-xs">Loading authorized citizen records…</span>
        </div>
      ) : cases.length === 0 ? (
        <div className="py-16 text-center bg-slate-900/60 rounded-2xl border border-slate-800 p-8">
          <FolderOpen size={40} className="mx-auto text-slate-400 mb-3" />
          <h3 className="text-sm font-bold text-slate-200">No Authorized Cases Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            There are no investigation records currently linked to your citizen profile. If you recently filed an FIR or complaint, please allow up to 24 hours for verification.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Case List Column */}
          <div className={`${selectedCase || detailLoading || detailError ? 'lg:col-span-6' : 'lg:col-span-12'} space-y-4`}>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Authorized Records ({cases.length})
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4">
              {cases.map((c) => {
                const isSelected = selectedCaseParam === c.case_id;

                return (
                  <div
                    key={c.case_id}
                    onClick={() => handleSelectCase(c.case_id)}
                    className={`p-5 rounded-xl border transition-all cursor-pointer relative ${
                      isSelected
                        ? 'bg-slate-900 border-teal-500/80 shadow-lg shadow-teal-950/40 ring-1 ring-teal-500/30'
                        : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-teal-400">
                          {c.case_id}
                        </span>
                        {c.fir_number && (
                          <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                            FIR: {c.fir_number}
                          </span>
                        )}
                      </div>

                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-teal-500/10 text-teal-300 border border-teal-500/30">
                        {c.status}
                      </span>
                    </div>

                    <h2 className="text-sm font-bold text-slate-100 mb-2">
                      {c.case_title}
                    </h2>

                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800/60 mb-3">
                      <div className="flex items-center gap-1.5 truncate">
                        <Calendar size={12} className="text-slate-400 shrink-0" />
                        <span>{c.date_opened || 'N/A'}</span>
                      </div>
                      <div className="flex items-center gap-1.5 truncate">
                        <Building size={12} className="text-slate-400 shrink-0" />
                        <span className="truncate">{c.police_station}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span className="text-indigo-300 font-medium">
                        {c.offence_category}
                      </span>
                      <span className="text-teal-400 text-xs font-semibold flex items-center gap-1">
                        View Details <ChevronRight size={13} />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Case Detail / Inspection Column */}
          {(selectedCase || detailLoading || detailError) && (
            <div className="lg:col-span-6 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5 sticky top-6 backdrop-blur-md">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wider">
                  <FileText size={15} className="text-teal-400" />
                  Official Case Dossier (Sanitized)
                </div>
                <button
                  onClick={handleClearSelection}
                  className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 cursor-pointer"
                  title="Close inspection"
                >
                  <X size={15} />
                </button>
              </div>

              {detailLoading ? (
                <div className="py-16 flex flex-col items-center justify-center text-slate-400 gap-2">
                  <Loader2 size={24} className="animate-spin text-teal-400" />
                  <span className="text-xs">Verifying case authorization…</span>
                </div>
              ) : detailError ? (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <AlertCircle size={14} />
                    Authorization Notice
                  </div>
                  <div>{detailError}</div>
                </div>
              ) : selectedCase ? (
                <div className="space-y-4 text-xs">
                  <div>
                    <span className="text-[10px] font-mono text-teal-400 font-bold uppercase block mb-1">
                      {selectedCase.case_id} • {selectedCase.offence_category}
                    </span>
                    <h2 className="text-base font-bold text-slate-100">
                      {selectedCase.case_title}
                    </h2>
                  </div>

                  <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block font-medium">Status</span>
                      <span className="text-teal-300 font-bold">{selectedCase.status}</span>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block font-medium">FIR Number</span>
                      <span className="text-slate-200 font-mono font-semibold">{selectedCase.fir_number || 'Under Process'}</span>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block font-medium">Registration Date</span>
                      <span className="text-slate-200">{selectedCase.date_opened || 'N/A'}</span>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block font-medium">Jurisdiction</span>
                      <span className="text-slate-200">{selectedCase.district}, {selectedCase.state}</span>
                    </div>

                    <div className="col-span-2">
                      <span className="text-[10px] text-slate-400 uppercase block font-medium">Designated Station</span>
                      <span className="text-slate-200 font-medium">{selectedCase.police_station}</span>
                    </div>
                  </div>

                  {/* Official Notice */}
                  <div className="p-4 bg-teal-950/20 border border-teal-500/30 rounded-xl text-teal-200/90 text-xs space-y-1.5">
                    <div className="font-bold text-teal-300 flex items-center gap-1.5">
                      <Info size={14} />
                      Official Department Advisory
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      {selectedCase.official_notice}
                    </p>
                    <div className="text-[10px] text-teal-400/80 pt-1 font-mono">
                      Authorized profile: {selectedCase.authorized_for_user}
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-[10px] text-slate-400 leading-relaxed">
                    <span className="font-semibold text-slate-300">Privacy Notice:</span> Detailed suspect relationships, analytical graph embeddings, and classified investigative leads are restricted to authorized investigating officers.
                  </div>
                </div>
              ) : null}
            </div>
          )}

        </div>
      )}
    </div>
  );
}
