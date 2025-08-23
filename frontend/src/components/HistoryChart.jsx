import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function HistoryChart() {
  const [data,setData] = useState([]);
  const load = ()=>{
    const cacheBuster = 't=' + Date.now();
    fetch(`./data/history.json?${cacheBuster}`, { cache: 'no-store' })
      .then(r=> r.ok ? r.json(): Promise.reject(r.statusText))
      .then(h=>{
        const series = h.series || [];
        setData(series.map(x=>({
          ts: (x.timestamp||'').slice(0,19).replace('T',' '),
          v: x.index_value
        })))
      })
      .catch(()=>{});
  };
  useEffect(()=>{
    load();
    const id = setInterval(load, 60*1000); // refresh every minute
    return ()=> clearInterval(id);
  },[]);
  return (
    <div className="h-80 w-full bg-neutral-900 border border-neutral-700 rounded-xl p-4">
      <div className="text-sm text-neutral-400 mb-2 flex items-center gap-2">Historical Index <span className="text-[10px] text-neutral-600">(auto-refresh)</span></div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="ts" hide/>
            <YAxis domain={[0,100]} tick={{fill:'#999', fontSize:12}} />
            <Tooltip contentStyle={{background:'#111', border:'1px solid #333'}} />
            <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" />
            <Line type="monotone" dataKey="v" stroke="#6B8AFF" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}