import React from 'react';

export default function ComponentCard({ c }){
  if(!c) return null;
  const score = typeof c.score === 'number' ? c.score.toFixed(1) : '–';
  return (
    <div className="rounded-lg border border-emerald-500/40 bg-slate-800/50 hover:bg-slate-800 transition-colors px-4 py-3 flex flex-col gap-1">
      <div className="text-[13px] font-medium text-slate-200 flex flex-wrap gap-1 items-baseline">
        <span>{c.name}</span>
        <span className="text-slate-400 text-[11px]">({c.symbol})</span>
      </div>
      <div className="text-emerald-300 font-semibold text-lg leading-none">{score}</div>
      <div className="text-[11px] text-slate-400">Weight: {(c.weight*100).toFixed(1)}%</div>
    </div>
  );
}
