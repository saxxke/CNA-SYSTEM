import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

/**
 * SuggestedFollowups.jsx
 * Clickable investigation query suggestions provided directly by the backend payload.
 */
export default function SuggestedFollowups({ suggestions = [], onSelectSuggestion }) {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="mt-3 pt-2.5 border-t border-slate-800/80">
      <span className="text-[11px] uppercase font-bold tracking-wider text-slate-400 block mb-2 flex items-center gap-1.5">
        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
        Suggested Follow-up Inquiries
      </span>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((sug, idx) => (
          <button
            key={idx}
            onClick={() => onSelectSuggestion(sug)}
            className="px-2.5 py-1 text-xs rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 hover:border-slate-600 transition-all flex items-center gap-1.5 text-left group"
          >
            <span>{sug}</span>
            <ArrowRight className="w-3 h-3 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
          </button>
        ))}
      </div>
    </div>
  );
}
