/**
 * GraphControls — Viewport and layout controls for Cytoscape.js canvas.
 */
import React from 'react';
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Crosshair } from 'lucide-react';

export default function GraphControls({ cyRef, onResetLayout }) {
  const zoomIn = () => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  };

  const zoomOut = () => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.zoom({ level: cy.zoom() / 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  };

  const fitGraph = () => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.fit(undefined, 30);
  };

  const centerSelected = () => {
    const cy = cyRef.current;
    if (!cy) return;
    const selected = cy.$(':selected');
    if (selected.length > 0) {
      cy.fit(selected, 80);
    } else {
      cy.fit(undefined, 30);
    }
  };

  const btnClass =
    'flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 ' +
    'text-slate-300 hover:text-white hover:bg-slate-800 hover:border-slate-700 transition-colors shadow-sm';

  return (
    <div className="grid grid-cols-2 gap-1.5">
      <button className={btnClass} onClick={zoomIn} title="Zoom In (+)">
        <ZoomIn size={13} className="text-slate-400" />
        <span>Zoom In</span>
      </button>
      <button className={btnClass} onClick={zoomOut} title="Zoom Out (-)">
        <ZoomOut size={13} className="text-slate-400" />
        <span>Zoom Out</span>
      </button>
      <button className={btnClass} onClick={fitGraph} title="Fit all elements to viewport">
        <Maximize2 size={13} className="text-slate-400" />
        <span>Fit View</span>
      </button>
      <button className={btnClass} onClick={centerSelected} title="Center on selected node">
        <Crosshair size={13} className="text-slate-400" />
        <span>Center</span>
      </button>
      <button 
        className={`${btnClass} col-span-2 text-indigo-300 border-indigo-900/50 hover:bg-indigo-950/40`} 
        onClick={onResetLayout} 
        title="Reset graph physics layout"
      >
        <RotateCcw size={13} className="text-indigo-400" />
        <span>Reset Graph Layout</span>
      </button>
    </div>
  );
}
