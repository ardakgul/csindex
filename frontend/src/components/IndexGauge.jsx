import React from 'react';

export default function IndexGauge({ value=50, sentiment='Neutral' }) {
  const color = value >= 75 ? 'text-green-400' : value >= 51 ? 'text-emerald-300' : value >=50 ? 'text-yellow-400' : value >=25 ? 'text-orange-400' : 'text-red-500';
  return (
    <div className="p-6 rounded-xl bg-neutral-900 border border-neutral-700 flex flex-col items-center gap-2">
      <div className={`text-6xl font-bold ${color}`}>{value.toFixed(2)}</div>
      <div className="uppercase tracking-wide text-sm text-neutral-400">Cloudy&Shiny Index</div>
      <div className="text-sm font-medium text-neutral-300">{sentiment}</div>
    </div>
  );
}