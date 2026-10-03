import { useState } from 'react';
import { Bed, Bath, Ruler, MapPin, Search, Building2 } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { properties, stats, features } from './data/mockData';

const PROP_IMGS = [
  img.realestate.prop1,
  img.realestate.prop2,
  img.realestate.prop3,
  img.realestate.prop4,
  img.realestate.prop5,
  img.realestate.prop6,
];

const featureIconMap = { search: Search, map: MapPin, shield: Building2, key: Building2 };

export default function PropertyListing() {
  const [activeType, setActiveType] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = properties.filter((p) => {
    const matchType = activeType === 'All' || p.type === activeType;
    const matchSearch =
      p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.location.toLowerCase().includes(searchTerm.toLowerCase());
    return matchType && matchSearch;
  });

  return (
    <TemplateShell
      title="Real Estate Listings"
      description="Browse, filter, and discover premium properties."
      category="Real Estate"
      actions={
        <Button size="sm">
          <Building2 className="h-4 w-4 mr-1" />
          List Property
        </Button>
      }
    >
      {/* Hero with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-64 mb-6">
        <img
          src={img.realestate.hero}
          alt="Properties"
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchPriority="high"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/30 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <Badge variant="info" className="mb-2 w-fit">
            🏠 2,840+ Verified Listings
          </Badge>
          <h2 className="font-display text-3xl font-bold text-white">Find Your Dream Home</h2>
          <p className="mt-1 text-white/80 text-sm max-w-xl">
            Verified apartments, villas, offices & plots across Pakistan's top cities.
          </p>
          <div className="relative max-w-sm mt-4 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by location..."
                className="w-full rounded-xl border border-border bg-background/90 pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <Button size="sm">Search</Button>
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

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        {['All', 'For Sale', 'For Rent'].map((t) => (
          <button
            key={t}
            onClick={() => setActiveType(t)}
            className={cn(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all',
              activeType === t
                ? 'bg-primary text-primary-foreground shadow-glow-sm'
                : 'bg-card border border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {t}
          </button>
        ))}
        <span className="ml-auto text-sm text-muted-foreground self-center">
          {filtered.length} properties
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((prop, i) => (
          <Card
            key={prop.id}
            animate="fade-up"
            animationDelay={i * 70}
            className="hover-lift group cursor-pointer"
            padding="none"
          >
            <div className="relative h-48 overflow-hidden rounded-t-lg">
              <img
                src={PROP_IMGS[i % PROP_IMGS.length]}
                alt={prop.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
              <div className="absolute top-3 left-3 flex gap-2">
                <span
                  className={cn(
                    'px-2 py-0.5 rounded-full text-xs font-bold backdrop-blur',
                    prop.type === 'For Sale'
                      ? 'bg-indigo-500/90 text-white'
                      : 'bg-emerald-500/90 text-white'
                  )}
                >
                  {prop.type}
                </span>
                {prop.tag && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500/90 backdrop-blur text-white">
                    {prop.tag}
                  </span>
                )}
              </div>
            </div>
            <div className="p-4">
              <h3 className="font-display font-bold text-sm mb-1 group-hover:text-primary transition-colors">
                {prop.title}
              </h3>
              <p className="flex items-center gap-1 text-xs text-muted-foreground mb-3">
                <MapPin className="h-3 w-3" />
                {prop.location}
              </p>
              <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                {prop.beds > 0 && (
                  <span className="flex items-center gap-1">
                    <Bed className="h-3.5 w-3.5" />
                    {prop.beds}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Bath className="h-3.5 w-3.5" />
                  {prop.baths}
                </span>
                <span className="flex items-center gap-1">
                  <Ruler className="h-3.5 w-3.5" />
                  {prop.area}
                </span>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <span className="font-display font-bold text-primary">{prop.price}</span>
                <Button size="sm" variant="outline" className="h-7 text-xs px-3">
                  View Details
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
