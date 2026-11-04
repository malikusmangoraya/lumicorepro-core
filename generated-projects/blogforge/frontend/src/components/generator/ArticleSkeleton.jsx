import React from 'react';

/** Shimmering skeleton shown while the AI is composing (no blank screens). */
const lines = [
  'w-11/12', 'w-full', 'w-full', 'w-9/12', 'w-full', 'w-10/12',
  'w-full', 'w-8/12', 'w-11/12', 'w-full', 'w-9/12', 'w-10/12',
];

export default function ArticleSkeleton() {
  return (
    <div className="max-w-3xl space-y-6" data-testid="gen-skeleton" aria-hidden="true">
      <div className="h-9 w-3/4 rounded-lg bg-slate-700/40 animate-shimmer" />
      {[0, 1, 2, 3].map((group) => (
        <div key={group} className="space-y-3">
          <div className="h-5 w-1/2 rounded-md bg-slate-700/40 animate-shimmer" />
          {lines.slice(group * 3, group * 3 + 3).map((w, i) => (
            <div key={i} className={`h-4 ${w} rounded-md bg-slate-800/80 animate-shimmer`} style={{ animationDelay: `${(group * 3 + i) * 90}ms` }} />
          ))}
        </div>
      ))}
    </div>
  );
}
