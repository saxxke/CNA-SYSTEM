import React from 'react';

export default function PriorityBadge({ level }) {
  const styles = {
    HIGH: 'bg-rose-950/80 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-950/50',
    MEDIUM: 'bg-amber-950/80 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-950/50',
    LOW: 'bg-sky-950/80 text-sky-300 border-sky-500/40 shadow-sm shadow-sky-950/50',
    UNKNOWN: 'bg-slate-800 text-slate-300 border-slate-700',
  };
  
  const selectedStyle = styles[level?.toUpperCase()] || styles.UNKNOWN;
  
  return (
    <span className={`px-2.5 py-0.5 inline-flex items-center text-[11px] font-mono font-bold tracking-wider rounded-md border ${selectedStyle}`}>
      {level || 'UNKNOWN'}
    </span>
  );
}
