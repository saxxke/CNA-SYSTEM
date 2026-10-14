import React, { useState, useRef, useEffect } from 'react';
import { Bot, ShieldAlert, Sparkles, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import api from '../api/client';
import AssistantWelcome from '../components/assistant/AssistantWelcome';
import ChatMessage from '../components/assistant/ChatMessage';
import ChatInput from '../components/assistant/ChatInput';

/**
 * AssistantPage.jsx
 * Primary investigator-facing conversational AI assistant page.
 * Strictly communicates with POST /api/assistant/query.
 */
export default function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activePersonId, setActivePersonId] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Submit inquiry to backend
  const handleSendMessage = async (questionText, explicitPersonId = null, explicitCaseId = null) => {
    if (!questionText || !questionText.trim()) return;

    setError(null);
    const userMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: questionText.trim()
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      // Prepare bounded conversation context (last 6 messages)
      const recentContext = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content || m.response?.answer_markdown || ''
      }));

      const payload = {
        question: questionText.trim(),
        active_case_id: explicitCaseId || activeCaseId || null,
        active_person_id: explicitPersonId || activePersonId || null,
        conversation_context: recentContext
      };

      const res = await api.post('/api/assistant/query', payload);
      const assistantData = res.data;

      // Update active person or case scope if returned in structured query
      if (assistantData.structured_query?.person_id) {
        setActivePersonId(assistantData.structured_query.person_id);
      }
      if (assistantData.structured_query?.case_id) {
        setActiveCaseId(assistantData.structured_query.case_id);
      }

      const assistantMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        response: assistantData
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Assistant query failed:', err);
      const rawDetail = err.response?.data?.detail;
      const detailMsg = typeof rawDetail === 'string'
        ? rawDetail
        : Array.isArray(rawDetail)
        ? rawDetail.map((d) => d.msg || JSON.stringify(d)).join(', ')
        : 'Unable to retrieve investigation data. Please check connection and try again.';
      setError(detailMsg);

      const errorMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        response: {
          intent: 'ERROR',
          answer_markdown: `⚠️ **Investigation Query Notice**:\n\n${detailMsg}\n\n*The backend deterministic pipeline encountered an issue. No analytical facts were altered.*`,
          safety_notice: 'SYNTHETIC DEMONSTRATION DATA • System error boundary'
        }
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCandidate = (personId, fullName) => {
    // User picked a candidate: send an explicit query binding the person ID
    setActivePersonId(personId);
    handleSendMessage(`Tell me about ${personId}`, personId);
  };

  const handleClearConversation = () => {
    setMessages([]);
    setError(null);
    setActivePersonId(null);
    setActiveCaseId(null);
  };

  const handleClearContext = (type) => {
    if (type === 'person') setActivePersonId(null);
    if (type === 'case') setActiveCaseId(null);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Header Bar */}
      <div className="border-b border-slate-800 bg-slate-900/80 px-4 py-3 shrink-0 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
              AI Investigation Assistant
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-950 text-blue-400 border border-blue-800">
                Grounded MVP
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Natural-language queries against verified cases, entities, and network graph services
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2">
          <span className="text-xs text-slate-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Backend Engine Online
          </span>
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="bg-amber-950/20 border-b border-amber-500/20 px-4 py-2 flex items-center gap-2 text-xs text-amber-300/90 shrink-0">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span className="truncate">
          <strong>SYNTHETIC DEMONSTRATION DATA:</strong> Analytical lead only. Requires human verification. Does not establish legal criminality or guilt.
        </span>
      </div>

      {/* Main Conversation Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <AssistantWelcome onSelectPrompt={(prompt) => handleSendMessage(prompt)} />
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onSelectCandidate={handleSelectCandidate}
              onAskFollowup={(q) => handleSendMessage(q)}
            />
          ))
        )}

        {/* Loading / Typing Indicator */}
        {loading && (
          <div className="flex items-start gap-3 max-w-4xl mx-auto">
            <div className="w-8 h-8 rounded-full bg-blue-950 border border-blue-700/60 flex items-center justify-center shrink-0 text-blue-400 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl rounded-tl-none bg-slate-900 border border-slate-800 text-slate-300 text-xs flex items-center gap-2.5 shadow-sm">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
              <span>Querying verified investigation services and synthesizing grounded facts...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Fixed Chat Input Area */}
      <ChatInput
        onSendMessage={(q) => handleSendMessage(q)}
        loading={loading}
        onClearConversation={messages.length > 0 ? handleClearConversation : null}
        activePersonId={activePersonId}
        activeCaseId={activeCaseId}
        onClearContext={handleClearContext}
      />
    </div>
  );
}
