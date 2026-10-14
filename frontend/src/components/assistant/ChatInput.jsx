import React, { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw, Sparkles, X, User, FolderOpen } from 'lucide-react';

/**
 * ChatInput.jsx
 * Fixed bottom input interface for submitting natural-language investigation inquiries.
 */
export default function ChatInput({
  onSendMessage,
  loading = false,
  onClearConversation,
  activePersonId,
  activeCaseId,
  onClearContext
}) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-slate-800 bg-slate-900/95 backdrop-blur-sm p-3 sm:p-4">
      <div className="max-w-4xl mx-auto space-y-2">
        {/* Active Context Chips if pinned */}
        {(activePersonId || activeCaseId) && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Context Scope:</span>
            {activePersonId && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[11px] font-mono">
                <User className="w-3 h-3" />
                {activePersonId}
                <button
                  onClick={() => onClearContext?.('person')}
                  className="hover:text-white"
                  title="Remove person context"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {activeCaseId && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[11px] font-mono">
                <FolderOpen className="w-3 h-3" />
                {activeCaseId}
                <button
                  onClick={() => onClearContext?.('case')}
                  className="hover:text-white"
                  title="Remove case context"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          {onClearConversation && (
            <button
              type="button"
              onClick={onClearConversation}
              className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition-colors shrink-0"
              title="Reset Conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}

          <div className="flex-1 relative rounded-lg border border-slate-700 focus-within:border-blue-500 bg-slate-950/80 transition-all">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder="Ask an investigation question (e.g. 'Show kidnapping cases in Kolkata', 'Tell me about Arjun Mehta')..."
              className="w-full bg-transparent px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none max-h-32"
            />
          </div>

          <button
            type="submit"
            disabled={!input.trim() || loading}
            className={`p-2.5 rounded-lg font-medium transition-all shrink-0 flex items-center justify-center ${
              !input.trim() || loading
                ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30'
            }`}
            title="Send Query (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        <div className="flex items-center justify-between text-[11px] text-slate-500 px-1">
          <span>Press <strong>Enter</strong> to send • <strong>Shift+Enter</strong> for new line</span>
          <span>100% Deterministic Grounded Retrieval</span>
        </div>
      </div>
    </div>
  );
}
