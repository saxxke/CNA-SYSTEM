import React from 'react';
import { ShieldAlert, AlertCircle } from 'lucide-react';

export default function SafetyBanner() {
  return (
    <div className="bg-amber-950/80 border-b border-amber-600/30 text-amber-200 px-4 py-1.5 text-xs flex items-center justify-between z-50 select-none">
      <div className="flex items-center space-x-2 mx-auto sm:mx-0">
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 tracking-wider">
          SYNTHETIC DEMO DATA
        </span>
        <span className="font-medium text-amber-200/90 text-[11px] hidden sm:inline">
          Analytical decision-support prototype. Data is entirely fictional.
        </span>
      </div>
      <div className="hidden md:flex items-center space-x-2 text-[11px] text-amber-300/80 font-medium">
        <span>Analytical leads only • Requires human verification • Does not establish guilt or criminality</span>
      </div>
    </div>
  );
}
