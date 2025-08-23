import React, { useEffect, useState } from 'react';
import IndexGauge from '../components/IndexGauge.jsx';
import HistoryChart from '../components/HistoryChart.jsx';

const API_BASE = import.meta.env.VITE_API_BASE; // optional runtime API
// Raw GitHub master JSON (always updated by scheduled workflow) fallback
const DATA_URL = import.meta.env.VITE_DATA_URL || 'https://raw.githubusercontent.com/ardakgul/csindex/master/website/data/current_index.json';
const STATIC_JSON = './data/current_index.json'; // legacy embedded snapshot

export default function Dashboard(){
  const [current,setCurrent]=useState(null);
  const [loading,setLoading]=useState(true);
  const [prediction,setPrediction]=useState(null);
  const [predError,setPredError]=useState(null);

  useEffect(()=>{
    async function load(){
      // 1. Try live API if configured
      if (API_BASE) {
        try {
          const r = await fetch(`${API_BASE}/index/current`, { cache: 'no-store' });
          if (r.ok) {
            const d = await r.json();
            setCurrent(d); setLoading(false); return;
          }
        } catch(_) { /* ignore and fallback */ }
      }
      // 2. Fetch dynamic raw JSON (updates without redeploy)
      try {
        const rs = await fetch(DATA_URL + '?t=' + Date.now(), { cache: 'no-store' });
        if (rs.ok) {
            const d = await rs.json();
            setCurrent(d); setLoading(false); return;
        }
      } catch(_) { /* ignore */ }
      // 3. Fallback to embedded snapshot
      try {
        const rs2 = await fetch(STATIC_JSON + '?t=' + Date.now());
        if (rs2.ok) {
          const d = await rs2.json();
          setCurrent(d);
        }
      } catch(_) { /* ignore */ }
      setLoading(false);
    }
    load();
    const id = setInterval(load, 5 * 60 * 1000); // refresh every 5 min on static host
    return ()=> clearInterval(id);
  },[]);

  useEffect(()=>{
    fetch(`${API_BASE}/model/predict`).then(r=> r.ok ? r.json(): Promise.reject(r.statusText)).then(p=> setPrediction(p)).catch(()=>{});
  },[]);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Monarch Castle Technologies – Cloudy&Shiny Index</h1>
        <div className="text-sm text-neutral-400">Strategic Market Sentiment Dashboard</div>
      </header>
      {loading && <div>Loading...</div>}
      {current && (
        <div className="grid md:grid-cols-3 gap-6">
          <IndexGauge value={current.index_value} sentiment={current.sentiment} />
          <div className="md:col-span-2 flex flex-col gap-6">
            <HistoryChart apiBase={API_BASE} />
            <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700">
              <div className="text-sm text-neutral-400 mb-2">Components</div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                {current.components?.map(c=> (
                  <div key={c.symbol} className="p-2 rounded bg-neutral-800/60 flex flex-col">
                    <span className="font-medium">{c.symbol}</span>
                    <span className="text-neutral-400">{c.score.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700">
              <div className="text-sm text-neutral-400 mb-2">Predictions (Experimental)</div>
              {!prediction && !predError && <div className="text-xs text-neutral-500">Training / loading model...</div>}
              {predError && <div className="text-xs text-red-400">{predError}</div>}
              {prediction && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-neutral-400 text-xs uppercase">Next Hour</div>
                    <div className="text-brand font-semibold">{prediction.next_hour?.toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-neutral-400 text-xs uppercase">Next Day</div>
                    <div className="text-brand font-semibold">{prediction.next_day?.toFixed(2)}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <footer className="pt-10 text-center text-xs text-neutral-600">© {new Date().getFullYear()} Monarch Castle Technologies – Financial Intelligence Division</footer>
    </div>
  );
}