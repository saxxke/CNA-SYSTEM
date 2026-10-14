import React from 'react';
import { 
  Bot, Sparkles, Search, Users, FolderOpen, Network, 
  AlertTriangle, ShieldAlert, ArrowRight, HelpCircle 
} from 'lucide-react';

/**
 * AssistantWelcome.jsx
 * Initial investigation assistant welcome state with categorized prompt archetypes.
 */
export default function AssistantWelcome({ onSelectPrompt }) {
  const promptCategories = [
    {
      title: 'Person Search & Case Associations',
      icon: Users,
      color: 'text-blue-400',
      prompts: [
        'Show persons associated with kidnapping cases',
        'Show people whose phone number ends in 4895',
        'Find people linked to at least 3 associated cases'
      ]
    },
    {
      title: 'Subject Dossier & Analytical Priority',
      icon: AlertTriangle,
      color: 'text-amber-400',
      prompts: [
        'Tell me about Arjun Mehta',
        'What cases is Arjun Mehta associated with?',
        'Why is Arjun Mehta an investigation priority?'
      ]
    },
    {
      title: 'Network Analysis & Cross-Case Links',
      icon: Network,
      color: 'text-emerald-400',
      prompts: [
        'Show the network connections for Arjun Mehta',
        'Show kidnapping cases in Kolkata',
        'Which cases are connected through common persons?'
      ]
    },
    {
      title: 'Ambiguity Disambiguation Protocol',
      icon: HelpCircle,
      color: 'text-purple-400',
      prompts: [
        'Tell me about Arjun'
      ]
    }
  ];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      {/* Title & Badge */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950/60 border border-blue-800/60 text-blue-400 text-xs font-semibold uppercase tracking-wider">
          <Bot className="w-4 h-4" />
          <span>Grounded Decision-Support Assistant</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-100 tracking-tight">
          AI Investigation Assistant
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Query the synthetic investigation registry using natural language. Questions are converted into verified deterministic queries against cases, entities, and network graph services.
        </p>
      </div>

      {/* Safety Notice Banner */}
      <div className="p-3.5 rounded-lg bg-slate-900/90 border border-amber-500/30 flex items-start gap-3 text-xs text-slate-300">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-semibold text-amber-300 uppercase tracking-wider text-[11px] block">
            Synthetic Demonstration Data Only
          </span>
          <p className="text-slate-400 leading-relaxed">
            AI-assisted analytical lead for decision support. Requires human investigator verification. Does not establish legal criminality or guilt. Civilian family relationships are isolated and never treated as evidence of case involvement.
          </p>
        </div>
      </div>

      {/* Categorized Prompt Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {promptCategories.map((cat, idx) => (
          <div
            key={idx}
            className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2.5"
          >
            <div className="flex items-center gap-2">
              <cat.icon className={`w-4 h-4 ${cat.color}`} />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                {cat.title}
              </h4>
            </div>

            <div className="space-y-1.5">
              {cat.prompts.map((promptText, pIdx) => (
                <button
                  key={pIdx}
                  onClick={() => onSelectPrompt(promptText)}
                  className="w-full text-left p-2.5 rounded-md bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 hover:text-white border border-slate-700/50 hover:border-slate-600 transition-all flex items-center justify-between group"
                >
                  <span className="truncate pr-2">"{promptText}"</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
