import { useState } from 'react';
import {
  PartyPopper,
  Cake,
  Briefcase,
  Music,
  Check,
  Building2,
  CakeSlice,
  CalendarDays,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Tabs } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { packages, eventTypes, features } from './data/mockData';

const EVENT_ICONS = [PartyPopper, Cake, Briefcase];

export default function RestaurantEvents() {
  const [selected, setSelected] = useState(packages[1]);
  const [activeTab, setActiveTab] = useState('All');

  return (
    <TemplateShell
      title="Private Dining & Events"
      description="Weddings, corporate launches, and celebrations — hosted in style."
      category="Restaurant"
      actions={
        <Button size="sm">
          <CalendarDays className="h-4 w-4 mr-1" />
          Book an Event
        </Button>
      }
    >
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-52 mb-6">
        <img
          src={img.restaurant.hero}
          alt="Event venue"
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex items-end p-8">
          <div>
            <Badge className="mb-2 w-fit bg-orange-500/90">Now booking Winter Season</Badge>
            <h2 className="font-display text-3xl font-bold text-white">Celebrate With Us</h2>
            <p className="mt-1 text-white/80 text-sm max-w-xl">
              An elegant banquet, a fairy-lit lawn, and a kitchen that has fed three generations of
              families.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Packages */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-display text-lg font-bold">Choose Your Package</h3>
          {packages.map((p, i) => {
            const Icon = EVENT_ICONS[i];
            const active = selected?.name === p.name;
            return (
              <Card
                key={p.name}
                animate="fade-up"
                animationDelay={i * 80}
                className={cn(
                  'cursor-pointer transition-all border-2',
                  active ? 'border-primary shadow-glow-sm' : 'hover:border-primary/40'
                )}
                onClick={() => setSelected(p)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') setSelected(p);
                }}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={cn(
                      'h-11 w-11 rounded-xl flex items-center justify-center shrink-0',
                      active
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <h4 className="font-display font-semibold">{p.name}</h4>
                      <span className="font-display font-bold text-primary whitespace-nowrap">
                        {p.price}
                        <span className="text-xs text-muted-foreground font-medium"> /event</span>
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">{p.capacity}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {p.perks.map((perk) => (
                        <span
                          key={perk}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-muted text-[11px] font-medium"
                        >
                          <Check className="h-3 w-3 text-emerald-400" />
                          {perk}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
          <div className="flex flex-wrap gap-3">
            <Button size="lg">
              <CakeSlice className="h-4 w-4 mr-1" />
              Reserve Date
            </Button>
            <Button size="lg" variant="outline">
              <Building2 className="h-4 w-4 mr-1" />
              Schedule a Venue Tour
            </Button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Gallery */}
          <Card animate="fade-up" animationDelay={120}>
            <h4 className="font-display font-bold mb-3">Venue Gallery</h4>
            <div className="grid grid-cols-2 gap-2">
              <img
                src={img.restaurant.interior}
                alt="Banquet hall"
                className="h-24 w-full object-cover rounded-xl"
                loading="lazy"
                decoding="async"
              />
              <img
                src={img.restaurant.dish3}
                alt="Buffet setup"
                className="h-24 w-full object-cover rounded-xl"
                loading="lazy"
                decoding="async"
              />
              <img
                src={img.restaurant.dish5}
                alt="Gourmet catering"
                className="h-24 w-full object-cover rounded-xl"
                loading="lazy"
                decoding="async"
              />
              <img
                src={img.restaurant.hero}
                alt="Evening event"
                className="h-24 w-full object-cover rounded-xl"
                loading="lazy"
                decoding="async"
              />
            </div>
          </Card>
          {/* Features */}
          <Card animate="fade-up" animationDelay={200} padding="sm">
            <h4 className="font-display font-bold mb-3">Everything Included</h4>
            <ul className="space-y-3">
              {features.map((f) => (
                <li key={f.title} className="flex gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs">
                    <span className="font-semibold">{f.title}</span> —{' '}
                    <span className="text-muted-foreground">{f.desc}</span>
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      {/* Event types strip */}
      <div className="mt-8">
        <Tabs value={activeTab} onChange={setActiveTab} className="mb-4">
          {eventTypes.map((tab) => (
            <button
              key={tab}
              className={cn(
                'px-4 py-1.5 rounded-lg text-sm font-medium',
                activeTab === tab
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {tab}
            </button>
          ))}
        </Tabs>
        <Card padding="sm" className="flex items-center gap-4 flex-wrap">
          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Music className="h-5 w-5 text-primary" />
          </div>
          <p className="text-sm text-muted-foreground flex-1 min-w-[220px]">
            <span className="font-semibold text-foreground">Live entertainment included</span> —
            dhol for weddings, a DJ for receptions, and acoustic sets for corporate evenings.
          </p>
          <Badge variant="outline" className="text-[11px]">
            Up to 120 guests
          </Badge>
        </Card>
      </div>
    </TemplateShell>
  );
}
