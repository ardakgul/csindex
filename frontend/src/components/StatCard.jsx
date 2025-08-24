import React from 'react';

export default function StatCard({ label, value, sub }){
  return (
    <div className="rounded-xl bg-slate-800/60 backdrop-blur-sm border border-slate-700 px-4 py-3 flex flex-col gap-1 min-w-[130px]">
      <div className="text-2xl font-semibold text-emerald-300 tracking-tight">{value ?? '—'}</div>
      <div className="text-[11px] uppercase tracking-wide text-slate-400 font-medium">{label}</div>
      {sub && <div className="text-[10px] text-slate-500">{sub}</div>}
    </div>
  );
}
