import React, { useEffect, useState } from 'react';

export default function NewsSentiment(){
  const [data,setData]=useState(null);
  const load=()=>{
    fetch('/api/news/sentiment').then(r=>r.ok?r.json():Promise.reject()).then(setData).catch(()=>{});
  };
  useEffect(()=>{load(); const id=setInterval(load, 120000); return ()=>clearInterval(id);},[]);
  if(!data) return <div className="text-xs text-neutral-500">Loading news sentiment...</div>;
  return (
    <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700 flex flex-col gap-2">
      <div className="text-sm text-neutral-400">News Sentiment</div>
      <div className="text-3xl font-semibold">{typeof data.score==='number'? data.score.toFixed(2): 'N/A'}</div>
      <div className="text-xs text-neutral-500">Strength: {(data.sentiment_strength||0).toFixed(2)} • Headlines: {data.headlines_analyzed||0}</div>
      {data.sample_headlines && data.sample_headlines.length>0 && (
        <ul className="text-xs text-neutral-400 list-disc ml-4 space-y-1 max-h-40 overflow-auto pr-2">
          {data.sample_headlines.map((h,i)=>(<li key={i}>{h}</li>))}
        </ul>
      )}
    </div>
  );
}
