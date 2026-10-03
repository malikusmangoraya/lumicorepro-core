import { useState } from 'react';
import { Star, MapPin, Clock, Check, Sparkles } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { packages, types } from './data/mockData';

const PKG_IMGS = [
  img.travel.dest1,
  img.travel.dest2,
  img.travel.dest3,
  img.travel.dest4,
  img.travel.dest5,
  img.travel.dest6,
];

export default function TourPackages() {
  const [type, setType] = useState('All');
  const list = type === 'All' ? packages : packages.filter((p) => p.type === type);

  return (
    <TemplateShell
      title="Tour Packages"
      description="All-inclusive holidays — transport, stay, and experiences in one price."
      category="Travel"
      actions={
        <Button size="sm">
          <Sparkles className="h-4 w-4 mr-1" />
          Custom Trip Request
        </Button>
      }
    >
      {/* Type filter */}
      <div className="flex flex-wrap gap-2 mb-8">
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setType(t)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              type === t
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {list.map((p, i) => (
          <Card
            key={p.name}
            animate="fade-up"
            animationDelay={(i * 70) % 350}
            className="overflow-hidden flex flex-col"
          >
            <div className="relative h-44">
              <img
                src={PKG_IMGS[i % PKG_IMGS.length]}
                alt={p.name}
                className="h-full w-full object-cover"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
              <Badge className="absolute top-3 left-3 bg-primary/90 text-[10px]">{p.type}</Badge>
              <span className="absolute top-3 right-3 flex items-center gap-1 bg-black/60 backdrop-blur px-2 py-0.5 rounded-full text-xs font-bold text-amber-300">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                {p.rating}
              </span>
              <div className="absolute bottom-3 left-3">
                <p className="font-display font-bold text-white leading-snug">{p.name}</p>
                <p className="flex items-center gap-1 text-white/75 text-xs mt-0.5">
                  <MapPin className="h-3 w-3" />
                  {p.location}
                </p>
              </div>
            </div>
            <div className="p-4 flex flex-col flex-1">
              <div className="flex flex-wrap gap-1.5 mb-3">
                {p.highlights.map((h) => (
                  <Badge key={h} variant="outline" size="sm" className="text-[10px]">
                    <Check className="h-3 w-3 text-emerald-400 mr-1" />
                    {h}
                  </Badge>
                ))}
              </div>
              <div className="mt-auto flex items-center justify-between pt-3 border-t border-border/60">
                <div>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {p.duration}
                  </p>
                  <p className="font-display text-xl font-bold text-primary">
                    {p.price}
                    <span className="text-[10px] text-muted-foreground font-medium"> /person</span>
                  </p>
                </div>
                <Button size="sm">View Details</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <p className="text-center text-xs text-muted-foreground mt-6">
        All packages include 4×4 transport, 3-star-or-better stay, and a local diarist guide.
      </p>
    </TemplateShell>
  );
}
