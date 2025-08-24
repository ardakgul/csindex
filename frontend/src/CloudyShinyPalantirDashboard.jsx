// Cloudy & Shiny Index – Palantir‑style React Dashboard
// Requires: tailwindcss, recharts, React 18.
// Drop into existing project; uses /api/* endpoints with static fallback under /public/data/* when API fails.

import React, { useCallback, useEffect, useMemo, useRef, useState, Suspense } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer } from 'recharts';

// ---------- Types (JSDoc for JS project) ----------
/** @typedef {{ value:number, sentiment?:'bullish'|'bearish'|'neutral', last_calculated_at?:string, components_active?:number, calc_duration_ms?:number }} IndexCurrent */
/** @typedef {{ t:string, value:number }} IndexPoint */
/** @typedef {{ id:string, name:string, score:number, weight:number, group?:string }} ComponentRow */
/** @typedef {{ score:number, strength?:number, headlines?: { title:string, source?:string, url?:string, published_at?:string }[] }} SentimentItem */
/** @typedef {{ t:string, yhat:number, yhat_lower?:number, yhat_upper?:number }} PredictionPoint */
/** @typedef {{ horizon?:string, mape?:number, rmse?:number, last_trained_at?:string }} PredictMeta */

const qs = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
const DEBUG_DEFAULT = qs.get('debug') === '1';

const ts = () => Date.now();
const withCacheBust = (url) => url + (url.includes('?') ? '&' : '?') + 't=' + ts();

const getCache = (key) => { try { const raw = sessionStorage.getItem(key); return raw ? JSON.parse(raw) : null; } catch { return null; } };
const setCache = (key, val) => { try { sessionStorage.setItem(key, JSON.stringify(val)); } catch {} };

async function fetchWithFallback(apiPath, fallbackPath, init){
  try {
    const r = await fetch(withCacheBust(apiPath), { ...init, headers: { 'Accept':'application/json', ...(init && init.headers || {}) } });
    if(!r.ok) throw new Error('API ' + apiPath + ' ' + r.status);
    return await r.json();
  } catch (e){
    console.warn('API failed, using fallback', apiPath, e);
    const r2 = await fetch(withCacheBust(fallbackPath), { headers: { 'Accept':'application/json' }});
    if(!r2.ok) throw new Error('Fallback ' + fallbackPath + ' ' + r2.status);
    return await r2.json();
  }
}

function useAutoRefresh(key, loader, intervalMs, opts){
  const [data,setData] = useState(()=> getCache(key));
  const [loading,setLoading] = useState(!getCache(key));
  const [error,setError] = useState(null);
  const ref = useRef(null);
  const load = useCallback(async()=>{
    try { setError(null); setLoading(true); const d = await loader(); setData(d); setCache(key,d); }
    catch(err){ setError(err?.message||'error'); }
    finally { setLoading(false); }
  },[key,loader]);
  useEffect(()=>{ if(opts?.immediate !== false) load(); ref.current = setInterval(load, intervalMs); return ()=> ref.current && clearInterval(ref.current); },[intervalMs,load,opts?.immediate]);
  return { data, loading, error, reload: load };
}

function Gauge({ value=50, min=0, max=100, sentiment='neutral' }){
  const pct = Math.max(0, Math.min(1, (value - min)/(max-min)));
  const angle = -120 + pct*240;
  const color = sentiment==='bullish' ? 'fill-green-500' : sentiment==='bearish' ? 'fill-red-500' : 'fill-zinc-400';
  return <div className='w-full h-64 flex items-center justify-center'>
    <svg viewBox='0 0 200 120' className='w-full h-full'>
      <path d='M10,110 A90,90 0 0,1 190,110' className='stroke-zinc-700' strokeWidth='12' fill='none'/>
      {Array.from({length:13}).map((_,i)=>{ const a=(-120+i*20)*Math.PI/180; const x1=100+Math.cos(a)*78, y1=110+Math.sin(a)*78; const x2=100+Math.cos(a)*90, y2=110+Math.sin(a)*90; return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} className='stroke-zinc-500' strokeWidth={i%3===0?3:1}/>; })}
      <g transform={`rotate(${angle} 100 110)`}><polygon points='100,25 95,110 105,110' className={color} /></g>
      <circle cx={100} cy={110} r={6} className='fill-zinc-200'/>
      <text x={100} y={115} textAnchor='middle' className='fill-zinc-950 text-sm font-medium'>{Math.round(value)}</text>
      <text x={100} y={100} textAnchor='middle' className='fill-zinc-500 text-xs'>Cloudy & Shiny</text>
    </svg>
  </div>;
}

export default function CloudyShinyPalantirDashboard(){
  const [componentView,setComponentView] = useState('cards');
  const [sortKey,setSortKey] = useState('score');
  const [sortDir,setSortDir] = useState('desc');
  const [filter,setFilter] = useState('');
  const [debug,setDebug] = useState(DEBUG_DEFAULT);
  const [recalcStatus,setRecalcStatus] = useState('idle');
  const SCHEDULE_MINUTES = 30;

  const indexCurrent = useAutoRefresh('index_current', ()=> fetchWithFallback('/api/index/current','/data/index_current.json'), 60_000, { immediate:true });
  const indexHistory = useAutoRefresh('index_history', ()=> fetchWithFallback('/api/index/history','/data/index_history.json'), 120_000, { immediate:true });
  const components = useAutoRefresh('index_components', ()=> fetchWithFallback('/api/index/components','/data/index_components.json'), 180_000, { immediate:true });
  const sentiment = useAutoRefresh('news_sentiment', ()=> fetchWithFallback('/api/news/sentiment','/data/news_sentiment.json'), 180_000, { immediate:true });
  const prediction = useAutoRefresh('index_predict', ()=> fetchWithFallback('/api/index/predict','/data/index_predict.json'), 180_000, { immediate:true });

  const lastCalc = indexCurrent.data?.last_calculated_at ? new Date(indexCurrent.data.last_calculated_at) : null;
  const nextScheduled = useMemo(()=> lastCalc ? new Date(lastCalc.getTime() + SCHEDULE_MINUTES*60*1000) : null, [lastCalc]);

  const filteredComponents = useMemo(()=>{
    let arr = (components.data||[]).filter(c => (c.name?.toLowerCase().includes(filter.toLowerCase()) || c.id?.toLowerCase().includes(filter.toLowerCase())));
    arr = arr.sort((a,b)=>{ const dir = sortDir==='asc'?1:-1; if(sortKey==='name') return dir * a.name.localeCompare(b.name); if(sortKey==='score') return dir * (a.score - b.score); return dir * (a.weight - b.weight); });
    return arr;
  },[components.data, filter, sortDir, sortKey]);

  async function triggerRecalc(){
    setRecalcStatus('working');
    try { const r = await fetch(withCacheBust('/api/index/recalculate'), { method:'POST' }); if(!r.ok) throw new Error('Recalc '+r.status); setRecalcStatus('success'); indexCurrent.reload(); components.reload(); indexHistory.reload(); prediction.reload(); }
    catch(e){ console.error(e); setRecalcStatus('error'); }
    finally { setTimeout(()=> setRecalcStatus('idle'), 4000); }
  }

  return <div className='min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 font-inter'>
    <div className='sticky top-0 z-30 backdrop-blur bg-white/70 dark:bg-zinc-950/60 border-b border-zinc-200 dark:border-zinc-800'>
      <div className='mx-auto max-w-7xl px-4 py-3 flex items-center justify-between'>
        <div className='flex items-center gap-3'>
          <h1 className='text-xl font-semibold tracking-tight'>Cloudy & Shiny Index</h1>
          <span className='text-xs px-2 py-0.5 rounded-full bg-zinc-200 dark:bg-zinc-800'>Realtime</span>
        </div>
        <div className='flex items-center gap-2'>
          <button className='text-xs px-3 py-1.5 rounded-md bg-zinc-900 text-zinc-100 dark:bg-zinc-200 dark:text-zinc-900' onClick={()=>{ indexCurrent.reload(); indexHistory.reload(); components.reload(); sentiment.reload(); prediction.reload(); }}>Refresh</button>
          <button className='text-xs px-3 py-1.5 rounded-md border border-zinc-300 dark:border-zinc-700' onClick={()=> setDebug(d=>!d)}>Debug {debug? 'On':'Off'}</button>
        </div>
      </div>
    </div>
    <div className='mx-auto max-w-7xl px-4 py-2 grid grid-cols-1 md:grid-cols-3 gap-2 text-xs text-zinc-600 dark:text-zinc-400'>
      <div className='flex items-center gap-2'>Last calc: <span className='font-medium'>{lastCalc? lastCalc.toLocaleString() : '—'}</span></div>
      <div className='flex items-center gap-2'>Next (~{SCHEDULE_MINUTES}m): <span className='font-medium'>{nextScheduled? nextScheduled.toLocaleString(): '—'}</span></div>
      <div className='flex items-center gap-2'>Active components: <span className='font-medium'>{indexCurrent.data?.components_active ?? '—'}</span></div>
    </div>
    <main className='mx-auto max-w-7xl px-4 py-4 grid grid-cols-1 lg:grid-cols-3 gap-4'>
      <div className='col-span-1 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 p-4'>
        <div className='text-sm font-semibold mb-2'>Current Index</div>
        {indexCurrent.loading ? <div className='animate-pulse h-64 bg-zinc-200 dark:bg-zinc-800 rounded'/> : <Gauge value={indexCurrent.data?.value ?? 0} sentiment={indexCurrent.data?.sentiment || 'neutral'} />}
        <div className='mt-2 flex justify-between items-center text-sm'>
          <div>Sentiment: <span className='font-medium capitalize'>{indexCurrent.data?.sentiment || 'neutral'}</span></div>
          <button disabled={recalcStatus==='working'} onClick={triggerRecalc} className='px-3 py-1.5 rounded-md bg-zinc-900 text-white text-xs disabled:opacity-50'>Recalc</button>
        </div>
      </div>
      <div className='col-span-1 lg:col-span-2 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 p-4'>
        <div className='text-sm font-semibold mb-2'>Historical Trend</div>
        <div className='h-64'>{indexHistory.loading ? <div className='animate-pulse h-full bg-zinc-200 dark:bg-zinc-800 rounded'/> : <ResponsiveContainer width='100%' height='100%'>
          <LineChart data={indexHistory.data||[]} margin={{top:10,right:20,left:0,bottom:0}}>
            <CartesianGrid strokeDasharray='3 3'/>
            <XAxis dataKey='t' tick={{fontSize:12}} minTickGap={24}/>
            <YAxis tick={{fontSize:12}} domain={[0,100]}/>
            <RTooltip contentStyle={{fontSize:12}}/>
            <Line type='monotone' dataKey='value' dot={false} strokeWidth={2}/>
          </LineChart>
        </ResponsiveContainer>}</div>
      </div>
      <div className='col-span-1 lg:col-span-2 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 p-4'>
        <div className='flex justify-between items-center mb-3'>
          <div className='text-sm font-semibold'>Components</div>
          <div className='flex gap-2 items-center'>
            <select value={sortKey} onChange={e=>setSortKey(e.target.value)} className='text-xs bg-transparent border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1'>
              <option value='name'>Name</option>
              <option value='score'>Score</option>
              <option value='weight'>Weight</option>
            </select>
            <select value={sortDir} onChange={e=>setSortDir(e.target.value)} className='text-xs bg-transparent border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1'>
              <option value='asc'>Asc</option>
              <option value='desc'>Desc</option>
            </select>
            <input value={filter} onChange={e=>setFilter(e.target.value)} placeholder='Filter' className='text-xs px-2 py-1 rounded border border-zinc-300 dark:border-zinc-700 bg-transparent'/>
            <button onClick={()=> setComponentView(v=> v==='cards'?'table':'cards')} className='text-xs px-2 py-1 rounded border border-zinc-300 dark:border-zinc-700'>{componentView==='cards'?'Table':'Cards'}</button>
          </div>
        </div>
        {componentView==='cards' ? <div className='grid sm:grid-cols-2 xl:grid-cols-3 gap-3'>
          {filteredComponents.map(c=> <div key={c.id} className='p-3 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800'>
            <div className='flex justify-between items-center mb-1'>
              <div className='font-medium text-sm truncate' title={c.name}>{c.name}</div>
              <span className='text-[10px] px-1.5 py-0.5 rounded bg-zinc-200 dark:bg-zinc-700'>{c.group||'—'}</span>
            </div>
            <div className='grid grid-cols-2 gap-2 text-xs'>
              <div>Score<div className='font-semibold text-sm'>{c.score.toFixed(2)}</div></div>
              <div>Weight<div className='font-semibold text-sm'>{(c.weight*100).toFixed(1)}%</div></div>
            </div>
            <div className='mt-2 h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded overflow-hidden'><div className='h-full bg-zinc-900 dark:bg-zinc-100' style={{width: Math.min(100, Math.max(0,c.score))+'%'}}/></div>
          </div>)}
        </div> : <div className='overflow-auto max-h-80 border border-zinc-200 dark:border-zinc-700 rounded-lg'>
          <table className='min-w-full text-xs'>
            <thead className='bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300'>
              <tr><th className='text-left px-2 py-1'>Name</th><th className='text-left px-2 py-1'>ID</th><th className='text-right px-2 py-1'>Score</th><th className='text-right px-2 py-1'>Weight</th><th className='text-left px-2 py-1'>Group</th></tr>
            </thead>
            <tbody>{filteredComponents.map((c,i)=> <tr key={c.id} className={i%2? '':'bg-zinc-50 dark:bg-zinc-900'}>
              <td className='px-2 py-1'>{c.name}</td>
              <td className='px-2 py-1 font-mono'>{c.id}</td>
              <td className='px-2 py-1 text-right'>{c.score.toFixed(3)}</td>
              <td className='px-2 py-1 text-right'>{(c.weight*100).toFixed(2)}%</td>
              <td className='px-2 py-1'>{c.group||'—'}</td>
            </tr>)}</tbody>
          </table>
        </div>}
      </div>
      <div className='col-span-1 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 p-4'>
        <div className='text-sm font-semibold mb-2'>News Sentiment</div>
        {sentiment.loading ? <div className='animate-pulse h-40 bg-zinc-200 dark:bg-zinc-800 rounded'/> : <div className='space-y-3'>
          <div className='flex gap-6 text-sm'>
            <div>Score<div className='text-xl font-semibold'>{sentiment.data?.score?.toFixed?.(3) ?? '—'}</div></div>
            <div>Strength<div className='text-xl font-semibold'>{sentiment.data?.strength?.toFixed?.(3) ?? '—'}</div></div>
          </div>
          <div className='space-y-2 max-h-56 overflow-auto pr-1'>
            {sentiment.data?.headlines?.slice(0,10).map((h,i)=> <a key={i} rel='noreferrer' target='_blank' href={h.url} className='block p-2 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800'>
              <div className='text-xs font-medium line-clamp-2'>{h.title}</div>
              <div className='text-[10px] text-zinc-500'>{h.source || ''} {h.published_at? '• '+ new Date(h.published_at).toLocaleString(): ''}</div>
            </a>)}
          </div>
        </div>}
      </div>
      <div className='col-span-1 lg:col-span-3 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 p-4'>
        <div className='text-sm font-semibold mb-2'>Predictions</div>
        <div className='h-72'>{prediction.loading ? <div className='animate-pulse h-full bg-zinc-200 dark:bg-zinc-800 rounded'/> : <ResponsiveContainer width='100%' height='100%'>
          <AreaChart data={prediction.data?.forecast||[]} margin={{top:10,right:20,left:0,bottom:0}}>
            <CartesianGrid strokeDasharray='3 3'/>
            <XAxis dataKey='t' tick={{fontSize:12}} minTickGap={24}/>
            <YAxis tick={{fontSize:12}} domain={[0,100]}/>
            <RTooltip contentStyle={{fontSize:12}}/>
            <Area type='monotone' dataKey='yhat_lower' dot={false} opacity={0.15} />
            <Area type='monotone' dataKey='yhat_upper' dot={false} opacity={0.15} />
            <Line type='monotone' dataKey='yhat' dot={false} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>}</div>
        <div className='mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs'>
          <Metric label='Horizon' value={prediction.data?.meta?.horizon || '—'} />
            <Metric label='MAPE' value={prediction.data?.meta?.mape!=null ? (prediction.data.meta.mape*100).toFixed(2)+'%':'—'} />
            <Metric label='RMSE' value={prediction.data?.meta?.rmse!=null ? prediction.data.meta.rmse.toFixed(4):'—'} />
            <Metric label='Last Trained' value={prediction.data?.meta?.last_trained_at ? new Date(prediction.data.meta.last_trained_at).toLocaleString(): '—'} />
        </div>
      </div>
      <div className='col-span-1 lg:col-span-3 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 p-4'>
        <div className='text-sm font-semibold mb-2'>About the Index</div>
        <div className='prose prose-zinc dark:prose-invert max-w-none text-xs'>
          <p>The Cloudy & Shiny Index aggregates multi-domain signals (markets, on-chain, macro, news sentiment, activity) into a 0–100 score. Higher = risk-on (shiny), lower = risk-off (cloudy).</p>
          <ul>
            <li><b>Market Breadth:</b> advance/decline, volume, beta.</li>
            <li><b>On-chain:</b> transaction counts, fees, realized metrics.</li>
            <li><b>Macro:</b> yields, spreads, PMIs.</li>
            <li><b>News/Sentiment:</b> polarity & intensity of curated sources.</li>
            <li><b>Flows:</b> ETF flows, positioning data.</li>
          </ul>
          <p>50±5 = neutral. 65+ indicates elevated risk appetite; 35- suggests caution. Track rate of change and divergences vs. asset prices.</p>
        </div>
      </div>
    </main>
    {debug && <div className='fixed bottom-3 right-3 w-80 text-[10px] bg-white/90 dark:bg-zinc-900/90 backdrop-blur border border-zinc-200 dark:border-zinc-700 rounded-xl shadow p-2'>
      <div className='flex justify-between items-center mb-1'>
        <div className='font-semibold'>Debug</div>
        <button onClick={()=> setDebug(false)} className='px-1 rounded hover:bg-zinc-200 dark:hover:bg-zinc-700'>&times;</button>
      </div>
      <ul className='space-y-0.5'>
        <li>Last calc: <b>{lastCalc? lastCalc.toISOString():'—'}</b></li>
        <li>Next sched: <b>{nextScheduled? nextScheduled.toISOString():'—'}</b></li>
        <li>Active comps: <b>{indexCurrent.data?.components_active ?? '—'}</b></li>
        <li>History pts: <b>{indexHistory.data?.length || 0}</b></li>
        <li>Forecast pts: <b>{prediction.data?.forecast?.length || 0}</b></li>
        <li>Errors: <b>{[indexCurrent.error,indexHistory.error,components.error,sentiment.error,prediction.error].filter(Boolean).length}</b></li>
      </ul>
    </div>}
  </div>;
}

function Metric({ label, value }){ return <div className='rounded-lg border border-zinc-200 dark:border-zinc-700 p-2'>
  <div className='text-[10px] uppercase tracking-wide text-zinc-500'>{label}</div>
  <div className='text-sm font-semibold'>{value}</div>
</div>; }
