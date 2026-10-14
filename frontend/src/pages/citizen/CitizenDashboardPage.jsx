import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import api from '../../api/client';
import { 
  FolderOpen, Shield, Clock, CheckCircle, AlertCircle, 
  ArrowRight, PhoneCall, Info, Loader2, Building 
} from 'lucide-react';

export default function CitizenDashboardPage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchCitizenCases() {
      try {
        setLoading(true);
        // Strictly calls citizen-safe endpoint
        const res = await api.get('/api/citizen/cases');
        setCases(res.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load authorized case records.');
      } finally {
        setLoading(false);
      }
    }
    fetchCitizenCases();
  }, []);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-teal-950/40 via-slate-900/80 to-slate-900 border border-teal-500/30 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-semibold mb-3">
            <Shield size={13} />
            <span>Citizen Case Inquiry Portal</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Welcome, {currentUser?.display_name || 'Citizen'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Track official case progress and inquiries registered under your citizen identity.
            All records displayed below are verified and sanctioned for citizen review.
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Authorized Cases
            </span>
            <FolderOpen size={18} className="text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {loading ? <Loader2 size={20} className="animate-spin text-teal-400" /> : cases.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Linked to your verified identity
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Under Review / Active
            </span>
            <Clock size={18} className="text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {loading ? <Loader2 size={20} className="animate-spin text-amber-400" /> : cases.filter(c => c.status !== 'CLOSED').length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Official inquiry in progress
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Citizen Portal Status
            </span>
            <CheckCircle size={18} className="text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-emerald-400 mt-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Verified & Operational
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Live updates enabled
          </div>
        </div>
      </div>

      {/* Quick Cases Overview */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-md space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Your Registered Cases
            </h2>
            <p className="text-xs text-slate-400">
              Only cases explicitly authorized for your citizen profile are shown.
            </p>
          </div>
          <button
            onClick={() => navigate('/citizen/cases')}
            className="text-xs text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1 cursor-pointer transition-colors"
          >
            <span>View All Records</span>
            <ArrowRight size={13} />
          </button>
        </div>

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
            <Loader2 size={24} className="animate-spin text-teal-400" />
            <span className="text-xs">Fetching authorized case records…</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        ) : cases.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs bg-slate-950/40 rounded-lg border border-slate-800/80">
            No active case records currently authorized for this profile.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {cases.slice(0, 4).map((c) => (
              <div
                key={c.case_id}
                onClick={() => navigate(`/citizen/cases?caseId=${c.case_id}`)}
                className="p-4 bg-slate-950/70 border border-slate-800/90 hover:border-teal-500/50 rounded-xl transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs font-mono font-bold text-teal-400 group-hover:text-teal-300 transition-colors">
                    {c.case_id}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                    {c.status}
                  </span>
                </div>
                <h3 className="text-xs font-bold text-slate-100 mb-1 line-clamp-1">
                  {c.case_title}
                </h3>
                <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-2">
                  <Building size={12} className="text-slate-400" />
                  <span>{c.police_station} • {c.district}</span>
                </div>
                <div className="text-[10px] text-teal-400/80 font-medium">
                  {c.offence_category}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Official Citizen Assistance Banner */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
            <Info size={18} />
          </div>
          <div>
            <div className="font-bold text-slate-200">Need Immediate Police Assistance?</div>
            <div className="text-slate-400 text-[11px] mt-0.5">
              Dial national emergency helpline 112 or visit your designated local police station.
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-indigo-300 font-mono text-xs bg-indigo-950/40 border border-indigo-800/50 px-3 py-1.5 rounded-lg">
          <PhoneCall size={13} className="text-indigo-400" />
          <span>Helpline: 112 / 100</span>
        </div>
      </div>
    </div>
  );
}
