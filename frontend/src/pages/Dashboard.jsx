import React, { useEffect, useState } from 'react';
import IndexGauge from '../components/IndexGauge.jsx';
import HistoryChart from '../components/HistoryChart.jsx';

const DEBUG = new URLSearchParams(window.location.search).get('debug') === '1';

export default function Dashboard(){
  const [current,setCurrent]=useState(null);
  const [loading,setLoading]=useState(true);
  const [health,setHealth]=useState(null);

  const load = async()=>{
    const cacheBuster = 't=' + Date.now();
    try {
      const c = await fetch(`./data/current_index.json?${cacheBuster}`, { cache: 'no-store' });
      if (c.ok) {
        const d = await c.json();
        if (d && typeof d.index_value === 'number' && d.status !== 'error') {
          setCurrent(d);
        } else {
          // Keep existing current if value invalid; show fallback state
          setCurrent(d);
        }
      }
    } catch(_) {}
    try {
      const h = await fetch(`./data/health.json?${cacheBuster}`, { cache: 'no-store' });
      if (h.ok) setHealth(await h.json());
    } catch(_) {}
    setLoading(false);
  };

  useEffect(()=>{
    load();
    const id = setInterval(load, 60*1000); // refresh every minute
    return ()=> clearInterval(id);
  },[]);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Monarch Castle Technologies – Cloudy&Shiny Index</h1>
        <div className="text-sm text-neutral-400">Strategic Market Sentiment Dashboard</div>
      </header>
      {loading && <div>Loading...</div>}
      {!loading && !current && <div className="text-red-400 text-sm">No data available (yet). First scheduled run may still be pending.</div>}
      {current && (
        <div className="grid md:grid-cols-3 gap-6">
          <IndexGauge value={current.index_value} sentiment={current.sentiment} />
          <div className="md:col-span-2 flex flex-col gap-6">
            <HistoryChart />
            <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700">
              <div className="text-sm text-neutral-400 mb-2">Components</div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                {current.components?.map(c=> (
                  <div key={c.symbol} className="p-2 rounded bg-neutral-800/60 flex flex-col">
                    <span className="font-medium">{c.symbol}</span>
                    <span className="text-neutral-400">{typeof c.score === 'number' ? c.score.toFixed(1) : '–'}</span>
                  </div>
                ))}
                {!current.components?.length && <div className="text-neutral-500 text-xs col-span-full">No component detail in static mode.</div>}
              </div>
            </div>
            {DEBUG && (
              <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700 text-xs font-mono whitespace-pre-wrap">
                <div className="text-neutral-400 mb-2">Health Diagnostics</div>
                {health ? JSON.stringify(health,null,2) : 'No health.json loaded'}
              </div>
            )}
          </div>
        </div>
      )}
      <footer className="pt-10 text-center text-xs text-neutral-600">© {new Date().getFullYear()} Monarch Castle Technologies – Financial Intelligence Division</footer>
    </div>
  );
}