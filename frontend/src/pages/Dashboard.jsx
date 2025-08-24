import React, { useEffect, useState } from 'react';
import IndexGauge from '../components/IndexGauge.jsx';
import HistoryChart from '../components/HistoryChart.jsx';
import ComponentsTable from '../components/ComponentsTable.jsx';
import NewsSentiment from '../components/NewsSentiment.jsx';
import PredictionCard from '../components/PredictionCard.jsx';
import StatCard from '../components/StatCard.jsx';
import ComponentCard from '../components/ComponentCard.jsx';

const DEBUG = new URLSearchParams(window.location.search).get('debug') === '1';

export default function Dashboard(){
  const [current,setCurrent]=useState(null);
  const [loading,setLoading]=useState(true);
  const [health,setHealth]=useState(null);

  const load = async()=>{
    const cacheBuster = 't=' + Date.now();
    const apiBase = '/api/index';
    const tryPaths = [
      `${apiBase}/current?${cacheBuster}`,
      `./data/current_index.json?${cacheBuster}` // static fallback
    ];
    for (const url of tryPaths){
      try {
        const r = await fetch(url, {cache:'no-store'});
        if (r.ok){
          const d = await r.json();
            if (d && typeof d.index_value === 'number'){
              setCurrent(d);
              break;
            }
        }
      } catch(_){/* continue */}
    }
    try {
      const h = await fetch(`/api/index/health?${cacheBuster}`, { cache: 'no-store' });
      if (h.ok) setHealth(await h.json());
    } catch(_){
      // fallback static
      try {
        const h2 = await fetch(`./data/health.json?${cacheBuster}`, {cache:'no-store'});
        if (h2.ok) setHealth(await h2.json());
      } catch(_e){}
    }
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
        <div className="flex flex-col gap-8">
          <div className="grid md:grid-cols-4 gap-6 items-start">
            <div className="md:col-span-4 flex flex-col items-center gap-6 rounded-2xl bg-slate-900/70 border border-slate-700 p-8">
              <IndexGauge value={current.index_value} sentiment={current.sentiment} />
              <div className="w-full grid sm:grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="News Sentiment" value={(() => { const n=current.components?.find(c=>c.symbol==='NEWS_SENTIMENT'); return n? n.score.toFixed(1): '—'; })()} />
                <StatCard label="Active Components" value={current.active_components||current.components?.length} />
                <StatCard label="Historical Points" value={current.history_points || '—'} />
                <div className="rounded-xl bg-slate-800/60 border border-slate-700 p-2 flex flex-col justify-center"><PredictionCard /></div>
              </div>
            </div>
          </div>
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col gap-6">
              <HistoryChart />
              <NewsSentiment />
            </div>
            <div className="flex flex-col gap-4">
              <div className="grid sm:grid-cols-2 gap-3">
                {current.components?.filter(c=>c.symbol!=='NEWS_SENTIMENT').map(c=> <ComponentCard key={c.symbol} c={c} />)}
              </div>
              <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700 hidden">
                <ComponentsTable components={current.components||[]} />
              </div>
            </div>
          </div>
          {DEBUG && (
            <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700 text-xs font-mono whitespace-pre-wrap">
              <div className="text-neutral-400 mb-2">Health Diagnostics</div>
              {health ? JSON.stringify(health,null,2) : 'No health.json loaded'}
            </div>
          )}
        </div>
      )}
      <footer className="pt-10 text-center text-xs text-neutral-600">© {new Date().getFullYear()} Monarch Castle Technologies – Financial Intelligence Division</footer>
    </div>
  );
}