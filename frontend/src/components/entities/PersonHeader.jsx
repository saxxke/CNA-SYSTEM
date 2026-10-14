import React from 'react';
import { 
  User, Shield, MapPin, Briefcase, GraduationCap, 
  Calendar, Phone, Mail, Home, Network, ArrowLeft, 
  AlertCircle, ExternalLink, Sparkles
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PriorityBadge from '../common/PriorityBadge';

export default function PersonHeader({ profile, onBack }) {
  const navigate = useNavigate();

  if (!profile) return null;

  const demo = profile.demographics || {};
  const contact = profile.contact || {};
  const primaryAlias = profile.primary_alias;
  const aliases = profile.aliases || [];
  const networkSummary = profile.network_summary || {};
  const primaryCaseId = networkSummary.primary_case_id || 'CASE-001';
  const priority = profile.priority_information;

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm p-6 space-y-5 select-none">
      {/* Top action and navigation bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-indigo-400 transition-colors self-start"
        >
          <ArrowLeft size={15} />
          <span>Back to Person Directory</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">
            {profile.entity_id}
          </span>
          <button
            onClick={() => navigate(`/network?caseId=${primaryCaseId}`)}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-sm transition-all"
            title="Open person's primary case network graph"
          >
            <Network size={14} />
            <span>View Network</span>
          </button>
        </div>
      </div>

      {/* Main Profile Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
        <div className="flex items-start gap-4">
          {/* Avatar Icon */}
          <div className="w-16 h-16 rounded-2xl bg-indigo-950 border border-indigo-500/40 text-indigo-300 flex items-center justify-center font-bold text-2xl shadow-md shrink-0">
            {demo.full_name ? demo.full_name.charAt(0).toUpperCase() : 'P'}
          </div>

          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
                {demo.full_name}
              </h1>
              <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {profile.entity_id}
              </span>
              {priority && (
                <PriorityBadge level={priority.priority_level} />
              )}
            </div>

            {/* Aliases */}
            <div className="text-xs text-slate-400 flex flex-wrap items-center gap-2">
              {primaryAlias ? (
                <span>
                  Primary Alias: <strong className="text-slate-200">"{primaryAlias}"</strong>
                </span>
              ) : (
                <span>No registered alias</span>
              )}
              {aliases.length > 1 && (
                <span className="text-slate-400">
                  (also known as: {aliases.filter(a => a !== primaryAlias).join(', ')})
                </span>
              )}
            </div>

            {/* Primary Attributes */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-1">
              <div className="flex items-center gap-1.5">
                <MapPin size={13} className="text-slate-400" />
                <span>{contact.district || 'Chhattisgarh Area'}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Briefcase size={13} className="text-slate-400" />
                <span>{demo.occupation || 'Unspecified Occupation'}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar size={13} className="text-slate-400" />
                <span>{demo.gender} {demo.age ? `• ${demo.age}y` : ''}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Contact & Telecom Box */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3.5 space-y-2 text-xs min-w-[220px]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Registered Contact Data
          </div>
          <div className="flex items-center gap-2 font-mono text-slate-200">
            <Phone size={13} className="text-slate-400 shrink-0" />
            <span>{contact.primary_phone || 'None recorded'}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-400 truncate">
            <Mail size={13} className="text-slate-400 shrink-0" />
            <span>{contact.email || 'None on file'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
