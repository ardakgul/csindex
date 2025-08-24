import React from 'react';

export default function ComponentsTable({ components = [] }) {
  if (!components.length) {
    return <div className="text-neutral-500 text-xs">No components available.</div>;
  }
  return (
    <table className="w-full text-xs border-separate border-spacing-y-1">
      <thead className="text-neutral-400">
        <tr>
          <th className="text-left font-medium">Symbol</th>
          <th className="text-left font-medium">Name</th>
          <th className="text-right font-medium">Score</th>
          <th className="text-right font-medium">Weight</th>
        </tr>
      </thead>
      <tbody>
        {components.map(c => (
          <tr key={c.symbol} className="bg-neutral-800/40 hover:bg-neutral-800/70 transition-colors">
            <td className="py-1 px-2 font-medium">{c.symbol}</td>
            <td className="py-1 px-2 text-neutral-300">{c.name}</td>
            <td className="py-1 px-2 text-right">{typeof c.score === 'number' ? c.score.toFixed(2) : '–'}</td>
            <td className="py-1 px-2 text-right text-neutral-400">{(c.weight * 100).toFixed(1)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
