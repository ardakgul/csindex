import React, { useEffect, useState } from 'react';

export default function PredictionCard(){
  const [pred,setPred]=useState(null);
  const load=()=>{
    fetch('/api/index/predict').then(r=>r.ok?r.json():Promise.reject()).then(setPred).catch(()=>{});
  };
  useEffect(()=>{load(); const id=setInterval(load, 180000); return ()=>clearInterval(id);},[]);
  if(!pred) return <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700 text-xs text-neutral-500">Loading prediction...</div>;
  return (
    <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-700 flex flex-col gap-1">
      <div className="text-sm text-neutral-400">Forecast (next {pred.look_ahead_minutes}m)</div>
      <div className="text-2xl font-semibold">{pred.prediction !== null ? pred.prediction.toFixed(2): 'N/A'}</div>
      {pred.lower !== undefined && (
        <div className="text-[10px] text-neutral-500">CI 95%: {pred.lower} – {pred.upper}</div>
      )}
      <div className="text-[10px] text-neutral-600">Model: {pred.model}{pred.order ? ` (p=${pred.order})`: ''}</div>
      {pred.rmse && <div className="text-[10px] text-neutral-600">RMSE: {pred.rmse} R2: {pred.r2}</div>}
    </div>
  );
}
