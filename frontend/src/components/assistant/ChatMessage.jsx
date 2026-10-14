import React from 'react';
import { Bot, User, ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import SafeMarkdown from './SafeMarkdown';
import PersonResultCards from './PersonResultCards';
import CaseResultCards from './CaseResultCards';
import NetworkResultCards from './NetworkResultCards';
import PriorityResultCard from './PriorityResultCard';
import CandidateSelection from './CandidateSelection';
import ProvenancePanel from './ProvenancePanel';
import SuggestedFollowups from './SuggestedFollowups';

/**
 * ChatMessage.jsx
 * Comprehensive container for user and assistant messages in the investigation chat.
 * Converts structured backend response into readable analytical cards and audit trails.
 */
export default function ChatMessage({ message, onSelectCandidate, onAskFollowup }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex items-start justify-end gap-3 max-w-4xl mx-auto">
        <div className="max-w-xl p-3.5 rounded-2xl rounded-tr-none bg-blue-600 text-white text-sm shadow-md">
          <p className="leading-relaxed font-medium">{message.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0 border border-slate-600 text-slate-300">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  // Assistant message
  const resp = message.response || {};
  const {
    intent,
    response_state,
    structured_query,
    answer_markdown,
    provenance = [],
    persons = [],
    cases = [],
    network_relationships = [],
    priority_information,
    candidates = [],
    suggested_followups = [],
    safety_notice
  } = resp;

  return (
    <div className="flex items-start gap-3 max-w-4xl mx-auto">
      <div className="w-8 h-8 rounded-full bg-blue-950 border border-blue-700/60 flex items-center justify-center shrink-0 text-blue-400 mt-1">
        <Bot className="w-4 h-4" />
      </div>

      <div className="flex-1 space-y-3 min-w-0">
        <div className="p-4 rounded-2xl rounded-tl-none bg-slate-900 border border-slate-800 text-slate-200 shadow-sm space-y-3">
          {/* Header Bar with Intent & Filters */}
          {(intent || response_state) && (
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-800 text-xs">
              <div className="flex items-center gap-2">
                {intent && (
                  <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-blue-950 text-blue-300 border border-blue-800">
                    {intent}
                  </span>
                )}
                {response_state && (
                  <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${
                    response_state === 'MATCH_FOUND' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' :
                    response_state === 'NO_MATCH' ? 'bg-rose-950 text-rose-300 border-rose-800' :
                    response_state === 'CLARIFICATION_REQUIRED' ? 'bg-amber-950 text-amber-300 border-amber-800' :
                    'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
                    {response_state}
                  </span>
                )}
                {structured_query?.offence && (
                  <span className="text-[11px] text-slate-400">
                    Offence: <strong className="text-slate-200">{structured_query.offence}</strong>
                  </span>
                )}
                {structured_query?.location && (
                  <span className="text-[11px] text-slate-400">
                    Location: <strong className="text-slate-200">{structured_query.location}</strong>
                  </span>
                )}
                {structured_query?.min_case_count && (
                  <span className="text-[11px] text-slate-400">
                    Cases: <strong className="text-slate-200">&gt;= {structured_query.min_case_count}</strong>
                  </span>
                )}
              </div>
              <span className="text-[10px] text-slate-500">Deterministic Engine</span>
            </div>
          )}

          {/* Main Markdown Text */}
          {answer_markdown && (
            <SafeMarkdown content={answer_markdown} />
          )}

          {/* Candidate Disambiguation Cards (CLARIFICATION_REQUIRED) */}
          {candidates && candidates.length > 0 && (
            <CandidateSelection
              candidates={candidates}
              onSelectCandidate={onSelectCandidate}
            />
          )}

          {/* Person Results */}
          {persons && persons.length > 0 && (
            <PersonResultCards
              persons={persons}
              onAskFollowup={onAskFollowup}
            />
          )}

          {/* Case Results */}
          {cases && cases.length > 0 && (
            <CaseResultCards
              cases={cases}
              onAskFollowup={onAskFollowup}
            />
          )}

          {/* Network Relationships */}
          {network_relationships && network_relationships.length > 0 && (
            <NetworkResultCards
              relationships={network_relationships}
              activePersonId={structured_query?.person_id}
              activeCaseId={structured_query?.case_id}
            />
          )}

          {/* Priority Information */}
          {priority_information && (
            <PriorityResultCard
              priorityInfo={priority_information}
              personId={structured_query?.person_id}
              personName={structured_query?.person_name}
            />
          )}

          {/* Provenance & Audit Panel */}
          {provenance && provenance.length > 0 && (
            <ProvenancePanel provenance={provenance} />
          )}

          {/* Suggested Followups */}
          {suggested_followups && suggested_followups.length > 0 && (
            <SuggestedFollowups
              suggestions={suggested_followups}
              onSelectSuggestion={onAskFollowup}
            />
          )}

          {/* Safety Notice */}
          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-500 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-500/70 shrink-0" />
            <span>
              {safety_notice ||
                'Synthetic Demonstration Data. AI-assisted analytical lead. Requires human investigator verification.'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
