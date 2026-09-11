import { useState } from 'react';
import { Calendar, Users, Check, Clock, Sparkles, Coffee } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Input } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { slots, occasions, specials } from './data/mockData';

const DISH_IMGS = [img.restaurant.dish1, img.restaurant.dish3, img.restaurant.dish5];

export default function ReservationSystem() {
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [partySize, setPartySize] = useState(2);
  const [occasion, setOccasion] = useState(occasions[0]);
  const [confirmed, setConfirmed] = useState(false);

  return (
    <TemplateShell
      title="Table Reservation"
      description="Book a table in seconds — pick a time, party size, and occasion."
      category="Restaurant"
      actions={
        <Button size="sm">
          <Clock className="h-4 w-4 mr-1" />
          Open 12 PM – 12 AM
        </Button>
      }
    >
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-56 mb-6">
        <img
          src={img.restaurant.interior}
          alt="Dining room"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <Badge className="mb-2 w-fit bg-amber-500/90">
            Reserve Online &amp; Save 10% on the menu
          </Badge>
          <h2 className="font-display text-3xl font-bold text-white">Your Table Awaits</h2>
          <p className="mt-1 text-white/80 text-sm max-w-lg">
            Prime window tables, a private balcony, and a courtyard under fairy lights.
          </p>
        </div>
      </div>

      {confirmed ? (
        <Card animate="fade-up" className="text-center py-10 max-w-xl mx-auto">
          <div className="h-14 w-14 rounded-full bg-emerald-500/15 flex items-center justify-center mx-auto mb-4">
            <Check className="h-7 w-7 text-emerald-400" />
          </div>
          <h3 className="font-display text-2xl font-bold mb-2">Reservation Confirmed!</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Table for <span className="font-semibold text-foreground">{partySize}</span> ·{' '}
            {selectedSlot?.time} · {occasion}. A confirmation SMS is on its way.
          </p>
          <Button variant="outline" onClick={() => setConfirmed(false)}>
            Make Another Booking
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Booking form */}
          <Card animate="fade-up" className="lg:col-span-2">
            <h3 className="font-display font-bold mb-4 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              Book a table
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Full name
                </label>
                <Input placeholder="e.g. Ayesha Khan" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">Date</label>
                <Input type="date" defaultValue="2026-09-15" />
              </div>
            </div>

            {/* Party size */}
            <p className="text-xs font-medium text-muted-foreground mb-2">Party size</p>
            <div className="flex flex-wrap gap-2 mb-4">
              {[1, 2, 3, 4, 6, 8].map((n) => (
                <button
                  key={n}
                  onClick={() => setPartySize(n)}
                  className={cn(
                    'h-10 w-12 rounded-xl text-sm font-bold transition-all border',
                    partySize === n
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card border-border text-muted-foreground hover:border-primary/50'
                  )}
                >
                  {n}
                </button>
              ))}
            </div>

            {/* Occasion */}
            <p className="text-xs font-medium text-muted-foreground mb-2">Occasion</p>
            <div className="flex flex-wrap gap-2 mb-4">
              {occasions.map((o) => (
                <button
                  key={o}
                  onClick={() => setOccasion(o)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-xs font-medium transition-all border',
                    occasion === o
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card border-border text-muted-foreground hover:border-primary/50'
                  )}
                >
                  {o}
                </button>
              ))}
            </div>

            {/* Slots */}
            <p className="text-xs font-medium text-muted-foreground mb-2">Choose a time</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-6">
              {slots.map((s) => (
                <button
                  key={s.time}
                  disabled={!s.available}
                  onClick={() => setSelectedSlot(s)}
                  className={cn(
                    'rounded-xl border px-3 py-2 text-sm font-medium transition-all',
                    !s.available && 'opacity-40 cursor-not-allowed bg-muted',
                    s.available && selectedSlot?.time === s.time
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card border-border hover:border-primary/50'
                  )}
                >
                  <Clock className="h-3.5 w-3.5 inline mr-1" />
                  {s.time}
                </button>
              ))}
            </div>

            <Button
              size="lg"
              className="w-full sm:w-auto"
              disabled={!selectedSlot}
              onClick={() => setConfirmed(true)}
            >
              <Sparkles className="h-4 w-4 mr-1" />
              Confirm Reservation
            </Button>
          </Card>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card animate="fade-up" animationDelay={100} padding="sm">
              <h4 className="font-display font-bold mb-3 flex items-center gap-2">
                <Users className="h-4 w-4 text-primary" />
                Tonight's Specials
              </h4>
              <div className="space-y-3">
                {specials.map((s, i) => (
                  <div key={i} className="flex gap-3">
                    <img
                      src={DISH_IMGS[i % DISH_IMGS.length]}
                      alt={s.name}
                      className="h-12 w-12 rounded-xl object-cover shrink-0"
                    />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate">{s.name}</p>
                      <p className="text-xs text-muted-foreground line-clamp-2">{s.desc}</p>
                      <p className="text-xs font-bold text-primary mt-0.5">{s.price}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
            <Card animate="fade-up" animationDelay={150} padding="sm">
              <h4 className="font-display font-bold mb-2 flex items-center gap-2">
                <Coffee className="h-4 w-4 text-amber-400" />
                Good to know
              </h4>
              <ul className="space-y-1.5 text-xs text-muted-foreground">
                <li>• Free cancellation up to 2 hours before</li>
                <li>• Separate halal &amp; veg kitchens</li>
                <li>• Free valet parking after 6 PM</li>
              </ul>
            </Card>
          </div>
        </div>
      )}
    </TemplateShell>
  );
}
