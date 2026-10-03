import { useState } from 'react';
import { Star, Clock, MapPin, Plane, Search } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { destinations, tourTypes, stats, services } from './data/mockData';

const DEST_IMGS = [
  img.travel.dest1,
  img.travel.dest2,
  img.travel.dest3,
  img.travel.dest4,
  img.travel.dest5,
  img.travel.dest6,
];
const typeEmoji = { Adventure: '🏔️', Beach: '🏖️', Cultural: '🕌', Luxury: '✨' };

export default function TravelAgency() {
  const [activeType, setActiveType] = useState('All');
  const [search, setSearch] = useState('');

  const filtered = destinations.filter((d) => {
    const matchType = activeType === 'All' || d.type === activeType;
    const matchSearch =
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      d.country.toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  return (
    <TemplateShell
      title="Travel Agency"
      description="Explore tour packages, destinations & travel services."
      category="Travel"
      actions={
        <Button size="sm">
          <Plane className="h-4 w-4 mr-1" />
          Book Trip
        </Button>
      }
    >
      {/* Hero with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-64 mb-6">
        <img
          src={img.travel.hero}
          alt="Travel"
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchPriority="high"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-8 text-center">
          <Badge variant="info" className="mb-2">
            ✈️ 150+ Destinations Worldwide
          </Badge>
          <h2 className="font-display text-4xl font-bold text-white">Explore the World Your Way</h2>
          <p className="mt-1 text-white/80 text-sm max-w-xl">
            Curated packages, expert guides, and unforgettable journeys.
          </p>
          <div className="relative max-w-sm w-full mt-4 px-4">
            <Search className="absolute left-7 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search destination..."
              className="w-full rounded-xl border border-border bg-background/90 pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/50"
            />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {stats.map((s, i) => (
          <Card
            key={i}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center hover-lift"
          >
            <p className="font-display text-2xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Type Filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        {tourTypes.map((t) => (
          <button
            key={t}
            onClick={() => setActiveType(t)}
            className={cn(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all',
              activeType === t
                ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                : 'bg-card border border-border text-muted-foreground hover:border-sky-500/30'
            )}
          >
            {t !== 'All' ? `${typeEmoji[t]} ${t}` : t}
          </button>
        ))}
      </div>

      {/* Destinations */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((dest, i) => (
          <Card
            key={dest.id}
            animate="fade-up"
            animationDelay={i * 70}
            className="hover-lift group cursor-pointer"
            padding="none"
          >
            <div className="relative h-48 overflow-hidden rounded-t-lg">
              <img
                src={DEST_IMGS[i % DEST_IMGS.length]}
                alt={dest.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute top-3 left-3">
                {dest.badge && (
                  <span className="px-2 py-0.5 rounded-full bg-sky-500/90 backdrop-blur text-white text-xs font-bold">
                    {dest.badge}
                  </span>
                )}
              </div>
              <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur rounded-lg px-2 py-1 text-white text-xs font-bold">
                {dest.duration}
              </div>
            </div>
            <div className="p-4">
              <div className="flex items-start justify-between mb-1">
                <h3 className="font-display font-bold text-sm group-hover:text-primary transition-colors">
                  {dest.name}
                </h3>
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  {dest.rating}
                </span>
              </div>
              <p className="flex items-center gap-1 text-xs text-muted-foreground mb-3">
                <MapPin className="h-3 w-3" />
                {dest.country}
              </p>
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <span className="font-display font-bold text-primary">
                  {dest.price}{' '}
                  <span className="text-xs text-muted-foreground font-normal">/person</span>
                </span>
                <Button size="sm" className="h-7 text-xs px-3">
                  Book Now
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
