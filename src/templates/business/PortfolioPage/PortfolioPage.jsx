import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Button } from '@/components/ui';
import { projects, filters } from './data/mockData';

export default function PortfolioPage() {
  const [filter, setFilter] = useState('all');
  const list = projects.filter((p) => filter === 'all' || p.tag === filter);
  return (
    <TemplateShell title="Portfolio" description="Filterable project grid." category="Business">
      <div className="flex flex-wrap gap-2 mb-6">
        {filters.map((f) => (
          <Button
            key={f}
            size="sm"
            variant={filter === f ? 'primary' : 'outline'}
            onClick={() => setFilter(f)}
          >
            {f}
          </Button>
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {list.map((p, i) => (
          <article
            key={p.id}
            className="group overflow-hidden rounded-xl border border-border bg-card hover-lift animate-fade-in-up"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="aspect-[4/3] bg-gradient-to-br from-primary/20 to-muted transition-transform duration-500 group-hover:scale-105" />
            <div className="p-4">
              <p className="text-xs uppercase tracking-wide text-primary">{p.tag}</p>
              <h3 className="mt-1 font-display font-semibold">{p.title}</h3>
            </div>
          </article>
        ))}
      </div>
    </TemplateShell>
  );
}
