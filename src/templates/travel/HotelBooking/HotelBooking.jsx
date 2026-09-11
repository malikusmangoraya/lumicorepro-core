import { useState } from 'react';
import {
  MapPin,
  Star,
  Check,
  Search,
  CalendarDays,
  Users,
  Phone,
  Wifi,
  Utensils,
  Car,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Input } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { destinations, hotels, roomTypes, guests } from './data/mockData';

const HOTEL_IMGS = [
  img.travel.dest1,
  img.travel.dest2,
  img.travel.dest3,
  img.travel.dest4,
  img.travel.dest5,
];

export default function HotelBooking() {
  const [dest, setDest] = useState('All');
  const [guestsCount, setGuestsCount] = useState(2);
  const list = dest === 'All' ? hotels : hotels.filter((h) => h.city === dest);

  return (
    <TemplateShell
      title="Hotels & Stays"
      description="Handpicked stays with free cancellation on select rates."
      category="Travel"
      actions={
        <Button size="sm">
          <Phone className="h-4 w-4 mr-1" />
          Help · 24/7
        </Button>
      }
    >
      {/* Search hero */}
      <Card animate="fade-up" className="relative overflow-hidden mb-8">
        <div className="absolute inset-0">
          <img src={img.travel.hero} alt="Travel" className="h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/50 to-transparent" />
        </div>
        <div className="relative p-6 sm:p-8">
          <h2 className="font-display text-2xl font-bold text-white mb-4">Where to next?</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <select
                value={dest}
                onChange={(e) => setDest(e.target.value)}
                className="w-full rounded-xl border border-border bg-card pl-9 pr-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 appearance-none cursor-pointer"
              >
                <option>All destinations</option>
                {destinations.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </div>
            <div className="relative">
              <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input type="date" defaultValue="2026-09-20" className="pl-9" />
            </div>
            <div className="relative">
              <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input type="date" defaultValue="2026-09-23" className="pl-9" />
            </div>
            <div className="relative">
              <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <select
                value={guestsCount}
                onChange={(e) => setGuestsCount(Number(e.target.value))}
                className="w-full rounded-xl border border-border bg-card pl-9 pr-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 appearance-none cursor-pointer"
              >
                {guests.map((g) => (
                  <option key={g} value={g}>
                    {g} guest{g > 1 ? 's' : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <Button className="mt-4">
            <Search className="h-4 w-4 mr-1" />
            Search {guestsCount} guests
          </Button>
        </div>
      </Card>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {['All', ...destinations].map((d) => (
          <button
            key={d}
            onClick={() => setDest(d)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              dest === d
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {d}
          </button>
        ))}
      </div>

      {/* Hotel grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {list.map((h, i) => (
          <Card
            key={h.name}
            animate="fade-up"
            animationDelay={(i * 60) % 300}
            className="overflow-hidden flex flex-col"
          >
            <div className="relative h-44">
              <img
                src={HOTEL_IMGS[i % HOTEL_IMGS.length]}
                alt={h.name}
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              <span className="absolute top-3 right-3 flex items-center gap-1 bg-black/60 backdrop-blur px-2 py-0.5 rounded-full text-xs font-bold text-amber-300">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                {h.rating}
              </span>
              <div className="absolute bottom-3 left-3 flex items-center gap-1 text-white text-sm font-medium">
                <MapPin className="h-3.5 w-3.5" />
                {h.city}
              </div>
            </div>
            <div className="p-4 flex flex-col flex-1">
              <h3 className="font-display font-semibold leading-snug">{h.name}</h3>
              <div className="flex flex-wrap gap-1.5 mt-2 mb-4">
                {h.perks.map((p) => (
                  <Badge key={p} variant="outline" size="sm" className="text-[10px]">
                    <Check className="h-3 w-3 text-emerald-400 mr-1" />
                    {p}
                  </Badge>
                ))}
              </div>
              <div className="mt-auto flex items-center justify-between pt-3 border-t border-border/60">
                <div>
                  <p className="font-display text-lg font-bold">{h.price}</p>
                  <p className="text-[10px] text-muted-foreground">{h.nights}</p>
                </div>
                <Button size="sm">View Stays</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Amenities strip */}
      <Card
        animate="fade-up"
        padding="sm"
        className="mt-8 flex flex-wrap gap-5 items-center justify-center"
      >
        {[Wifi, Utensils, Car, Users].map((Icon, i) => (
          <span
            key={i}
            className="flex items-center gap-2 text-xs font-medium text-muted-foreground"
          >
            <Icon className="h-4 w-4 text-primary" />
            Free Wifi · Breakfast · Parking · Family Rooms
          </span>
        ))}
      </Card>
    </TemplateShell>
  );
}
