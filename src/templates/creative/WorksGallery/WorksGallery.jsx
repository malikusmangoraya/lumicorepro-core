import { useState } from 'react';
import { ArrowUpRight, Layers, Award } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { works, filters, stats } from './data/mockData';

const WORK_IMGS = {
  project1: img.creative.project1,
  project2: img.creative.project2,
  project3: img.creative.project3,
  project4: img.creative.project4,
};

export default function WorksGallery() {
  const [filter, setFilter] = useState('All');
  const list = filter === 'All' ? works : works.filter((w) => w.category === filter);

  return (
    <TemplateShell
      title="Selected Works"
      description="A working gallery of brand, digital, and still-life projects."
      category="Creative"
      actions={
        <Button size="sm">
          <Award className="h-4 w-4 mr-1" />9 Awards & Counting
        </Button>
      }
    >
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {stats.map((s, i) => (
          <Card
            key={s.label}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center"
          >
            <p className="font-display text-2xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
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

      {/* Masonry-ish grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {list.map((w, i) => (
          <Card
            key={w.title}
            animate="fade-up"
            animationDelay={(i * 80) % 300}
            className="overflow-hidden group"
          >
            <div className="relative h-64 overflow-hidden">
              <img
                src={WORK_IMGS[w.img]}
                alt={w.title}
                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-transparent" />
              <Badge variant="secondary" className="absolute top-3 left-3 text-[10px]">
                {w.category}
              </Badge>
              <span className="absolute bottom-3 left-3 text-white/75 text-xs">
                {w.client} · {w.year}
              </span>
              <button
                className="absolute bottom-3 right-3 h-9 w-9 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white group-hover:bg-primary transition-all"
                aria-label={`Open ${w.title}`}
              >
                <ArrowUpRight className="h-4 w-4" />
              </button>
            </div>
            <div className="p-4">
              <h3 className="font-display font-semibold">{w.title}</h3>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{w.desc}</p>
            </div>
          </Card>
        ))}
      </div>

      <Card
        padding="sm"
        animate="fade-up"
        className="mt-8 flex flex-wrap items-center gap-3 border-dashed"
      >
        <Layers className="h-5 w-5 text-primary shrink-0" />
        <p className="text-sm text-muted-foreground flex-1 min-w-[220px]">
          <span className="font-semibold text-foreground">Like the work?</span> Every project shown
          here is a real client deliverable. Let's make yours next.
        </p>
        <Button size="sm">Discuss Your Project</Button>
      </Card>
    </TemplateShell>
  );
}
