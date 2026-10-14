import React, { useEffect } from 'react';
import { X, User, Phone, MapPin, Briefcase, FileText, AlertCircle, Shield, ExternalLink } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export default function PersonPreviewModal({ person, onClose, onSelectCase }) {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!person) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh] transition-all transform animate-scaleUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow">
              {person.full_name ? person.full_name.charAt(0).toUpperCase() : 'P'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold tracking-tight text-white">{person.full_name}</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                  {person.person_id}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {person.primary_alias ? `Known alias: "${person.primary_alias}"` : 'Person of Interest Record'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            title="Close Preview"
          >
            <X size={18} />
          </button>
        </div>

        {/* Safety Notice Banner */}
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-start gap-2.5 text-xs text-amber-900">
          <AlertCircle size={15} className="text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Analytical Lead Only: </span>
            This record represents an investigative association derived from structured case data. Requires independent human verification.
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-sm">
          {/* Association in Current Case */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5">
            <div className="text-xs font-semibold uppercase text-slate-500 tracking-wider mb-1.5 flex items-center gap-1.5">
              <Shield size={13} className="text-indigo-600" />
              Role in Current Case
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
                {person.role || 'ASSOCIATE'}
              </span>
              <span className="text-xs text-slate-500">
                Source: {person.source || 'STRUCTURED_METADATA'}
              </span>
            </div>
            <p className="text-xs text-slate-600 italic">
              "{person.association_type || 'Associated with registered case record.'}"
            </p>
          </div>

          {/* Demographic & Location Details */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 border border-slate-100 rounded-lg bg-white shadow-sm">
              <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                <User size={13} /> Demographics
              </div>
              <div className="text-xs font-medium text-slate-800">
                {person.gender || 'Unknown'} • {person.age ? `${person.age} yrs` : 'Age N/A'}
              </div>
            </div>

            <div className="p-3 border border-slate-100 rounded-lg bg-white shadow-sm">
              <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                <Briefcase size={13} /> Occupation
              </div>
              <div className="text-xs font-medium text-slate-800 truncate">
                {person.occupation || 'Unspecified'}
              </div>
            </div>

            <div className="p-3 border border-slate-100 rounded-lg bg-white shadow-sm">
              <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                <MapPin size={13} /> Jurisdiction
              </div>
              <div className="text-xs font-medium text-slate-800 truncate">
                {person.city || person.district ? `${person.city || ''}${person.city && person.district ? ', ' : ''}${person.district || ''}` : 'Regional Area'}
              </div>
            </div>

            <div className="p-3 border border-slate-100 rounded-lg bg-white shadow-sm">
              <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                <Phone size={13} /> Telecom Contact
              </div>
              <div className="text-xs font-medium text-slate-800 font-mono truncate">
                {person.phones && person.phones.length > 0 ? person.phones[0] : 'No phone registered'}
              </div>
            </div>
          </div>

          {/* Linked Cases Cross-Index */}
          <div>
            <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <FileText size={13} className="text-slate-500" />
                Cross-Case Intelligence ({person.linked_cases ? person.linked_cases.length : 0} Linked Cases)
              </span>
            </div>
            
            {person.linked_cases && person.linked_cases.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1">
                {person.linked_cases.map((cid) => (
                  <button
                    key={cid}
                    onClick={() => {
                      onClose();
                      if (onSelectCase) onSelectCase(cid);
                    }}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-mono rounded bg-slate-100 text-indigo-700 hover:bg-indigo-50 hover:text-indigo-900 border border-slate-200 transition-colors"
                  >
                    <span>{cid}</span>
                    <ExternalLink size={10} className="text-slate-400" />
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No cross-case linkages indexed.</p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs">
          <div className="text-slate-500 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
            Synthetic Record
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onClose();
                navigate(`/entities/${person.person_id}`);
              }}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors flex items-center gap-1.5 text-xs"
            >
              <span>View Full Dossier</span>
              <ExternalLink size={12} />
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-slate-800 text-white hover:bg-slate-700 font-medium transition-colors text-xs"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
