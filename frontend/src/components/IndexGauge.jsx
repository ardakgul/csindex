import React from 'react';

export default function IndexGauge({ value=NaN, sentiment='Neutral' }) {
  const numeric = typeof value === 'number' && isFinite(value);
  const safeValue = numeric ? value : 0;
  const color = safeValue >= 75 ? 'text-green-400' : safeValue >= 51 ? 'text-emerald-300' : safeValue >=50 ? 'text-yellow-400' : safeValue >=25 ? 'text-orange-400' : 'text-red-500';
  return (
    <div className="p-6 rounded-xl bg-neutral-900 border border-neutral-700 flex flex-col items-center gap-2">
      <div className={`text-6xl font-bold ${color}`}>{numeric ? safeValue.toFixed(2) : 'N/A'}</div>
      <div className="uppercase tracking-wide text-sm text-neutral-400">Cloudy&Shiny Index</div>
      <div className="text-sm font-medium text-neutral-300">{numeric ? sentiment : 'Unavailable'}</div>
    </div>
  );
}