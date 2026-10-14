import React from 'react';

/**
 * SafeMarkdown.jsx
 * Pure React zero-dependency Markdown parser.
 * Renders headings, bold, inline code, lists, blockquotes, and paragraphs
 * WITHOUT using dangerouslySetInnerHTML, guaranteeing 100% XSS safety.
 */

function renderFormattedText(text, keyPrefix = 'fmt') {
  if (!text) return null;

  // Split by bold (**...**) and inline code (`...`)
  const tokens = [];
  const regex = /(\*\*.*?\*\*|`.*?`)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      tokens.push({ type: 'text', content: text.slice(lastIndex, match.index) });
    }
    const matchedStr = match[0];
    if (matchedStr.startsWith('**') && matchedStr.endsWith('**')) {
      tokens.push({ type: 'bold', content: matchedStr.slice(2, -2) });
    } else if (matchedStr.startsWith('`') && matchedStr.endsWith('`')) {
      tokens.push({ type: 'code', content: matchedStr.slice(1, -1) });
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    tokens.push({ type: 'text', content: text.slice(lastIndex) });
  }

  return tokens.map((token, idx) => {
    const key = `${keyPrefix}-${idx}`;
    if (token.type === 'bold') {
      return (
        <strong key={key} className="font-semibold text-slate-100">
          {token.content}
        </strong>
      );
    }
    if (token.type === 'code') {
      return (
        <code
          key={key}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-800 text-blue-300 font-mono text-xs border border-slate-700"
        >
          {token.content}
        </code>
      );
    }
    return <span key={key}>{token.content}</span>;
  });
}

export default function SafeMarkdown({ content, className = '' }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let currentList = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="list-disc list-inside space-y-1 my-2 text-slate-200">
          {currentList.map((item, i) => (
            <li key={`li-${i}`} className="text-sm leading-relaxed pl-1">
              {renderFormattedText(item, `li-fmt-${i}`)}
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      flushList();
      return;
    }

    // Unordered list item (- or *)
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      currentList.push(trimmed.slice(2));
      return;
    }

    // Numbered list item (e.g. "1. ")
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numberedMatch) {
      currentList.push(numberedMatch[2]);
      return;
    }

    flushList();

    // Headings
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={`h4-${idx}`} className="text-sm font-bold text-slate-100 uppercase tracking-wider mt-3 mb-1.5 flex items-center gap-2">
          {renderFormattedText(trimmed.slice(4), `h4-fmt-${idx}`)}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={`h3-${idx}`} className="text-base font-bold text-slate-100 mt-3 mb-1.5">
          {renderFormattedText(trimmed.slice(3), `h3-fmt-${idx}`)}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={`h2-${idx}`} className="text-lg font-bold text-blue-400 mt-3 mb-2">
          {renderFormattedText(trimmed.slice(2), `h2-fmt-${idx}`)}
        </h2>
      );
      return;
    }

    // Blockquote
    if (trimmed.startsWith('> ')) {
      elements.push(
        <blockquote
          key={`bq-${idx}`}
          className="border-l-2 border-blue-500/50 pl-3 py-1 my-1.5 text-xs text-slate-400 italic bg-slate-900/40 rounded-r"
        >
          {renderFormattedText(trimmed.slice(2), `bq-fmt-${idx}`)}
        </blockquote>
      );
      return;
    }

    // Regular paragraph
    elements.push(
      <p key={`p-${idx}`} className="text-sm text-slate-200 leading-relaxed my-1">
        {renderFormattedText(trimmed, `p-fmt-${idx}`)}
      </p>
    );
  });

  flushList();

  return <div className={`space-y-1 ${className}`}>{elements}</div>;
}
