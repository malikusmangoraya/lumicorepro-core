import { useState } from 'react';
import { ExternalLink, Folder, TrendingUp, ArrowUpRight } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { projects, filters, highlights } from './data/mockData';

const PROJECT_IMGS = {
  project1: img.portfolio.project1,
  project2: img.portfolio.project2,
  project3: img.portfolio.project3,
  code: img.portfolio.code,
};

export default function ProjectShowcase() {
  const [filter, setFilter] = useState('All');
  const list = filter === 'All' ? projects : projects.filter((p) => p.category === filter);

  return (
    <TemplateShell
      title="Selected Work"
      description="A few things I've shipped — with the numbers to back them up."
      category="Portfolio"
      actions={
        <Button size="sm">
          <ExternalLink className="h-4 w-4 mr-1" />
          Full Case Studies
        </Button>
      }
    >
      {/* Highlights */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {highlights.map((h, i) => (
          <Card
            key={h.label}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center"
          >
            <p className="font-display text-2xl font-bold text-primary">{h.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{h.label}</p>
          </Card>
        ))}
      </div>

      {/* Filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              filter === f
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {list.map((p, i) => (
          <Card
            key={p.name}
            animate="fade-up"
            animationDelay={(i * 80) % 300}
            className="overflow-hidden group"
          >
            <div className="relative h-52 overflow-hidden">
              <img
                src={PROJECT_IMGS[p.img]}
                alt={p.name}
                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
              <Badge className="absolute top-3 left-3">
                <Folder className="h-3 w-3 mr-1" />
                {p.category}
              </Badge>
              <span className="absolute bottom-3 left-3 text-white/75 text-xs">{p.year}</span>
            </div>
            <div className="p-5">
              <div className="flex items-center justify-between gap-2 mb-2">
                <h3 className="font-display text-lg font-bold">{p.name}</h3>
                <ArrowUpRight className="h-4 w-4 text-primary shrink-0 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{p.desc}</p>
              <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-border/60">
                {p.stack.map((s) => (
                  <Badge key={s} variant="outline" size="sm" className="text-[10px]">
                    {s}
                  </Badge>
                ))}
                <span className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-emerald-400">
                  <TrendingUp className="h-3.5 w-3.5" />
                  {p.outcome}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
