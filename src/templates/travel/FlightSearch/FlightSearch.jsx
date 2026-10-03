import { useState } from 'react';
import { Plane, Clock, Luggage, ChevronDown, ChevronUp, ArrowUpDown } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { routes, flights, filters } from './data/mockData';

export default function FlightSearch() {
  const [route, setRoute] = useState(routes[0]);
  const [stopFilter, setStopFilter] = useState('All');
  const [sortAsc, setSortAsc] = useState(true);
  const [expanded, setExpanded] = useState(null);

  const parsePrice = (p) => Number(p.replace(/[^0-9]/g, ''));
  let list = flights.filter((f) =>
    stopFilter === 'All' ? true : f.stops === (stopFilter === 'Non-stop' ? 0 : 1)
  );
  list = [...list].sort((a, b) =>
    sortAsc ? parsePrice(a.price) - parsePrice(b.price) : parsePrice(b.price) - parsePrice(a.price)
  );

  const [from, to] = route.split(' → ');

  return (
    <TemplateShell
      title="Search Flights"
      description="Compare live domestic fares with transparent pricing."
      category="Travel"
      actions={
        <Button size="sm">
          <Luggage className="h-4 w-4 mr-1" />
          Baggage Rules
        </Button>
      }
    >
      {/* Route header */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {routes.map((r) => (
          <button
            key={r}
            onClick={() => setRoute(r)}
            className={cn(
              'px-4 py-2.5 rounded-xl text-sm font-bold transition-all border',
              route === r
                ? 'bg-primary text-primary-foreground border-primary shadow-glow-sm'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            <Plane className="h-3.5 w-3.5 inline mr-1.5 -mt-px" />
            {r}
          </button>
        ))}
      </div>

      {/* Filters + sort */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {filters.stops.map((s) => (
          <button
            key={s}
            onClick={() => setStopFilter(s)}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-medium transition-all border',
              stopFilter === s
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {s} Flights
          </button>
        ))}
        <Button
          size="sm"
          variant="outline"
          className="ml-auto h-8 text-xs"
          onClick={() => setSortAsc((v) => !v)}
        >
          <ArrowUpDown className="h-3.5 w-3.5 mr-1" />
          Price {sortAsc ? 'Low → High' : 'High → Low'}
        </Button>
      </div>

      {/* Flights */}
      <div className="space-y-3">
        {list.map((f, i) => (
          <Card
            key={f.code}
            animate="fade-up"
            animationDelay={(i * 60) % 300}
            className="p-0 overflow-hidden"
          >
            <div className="p-5 flex flex-wrap items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                <Plane className="h-5 w-5 text-primary" />
              </div>
              <div className="min-w-[100px]">
                <p className="font-display font-bold">{f.airline}</p>
                <p className="text-xs text-muted-foreground">
                  {f.code} · {f.type}
                </p>
              </div>
              <div className="flex items-center gap-4 flex-1 min-w-[200px]">
                <div className="text-right">
                  <p className="font-display text-lg font-bold leading-tight">{f.dep}</p>
                  <p className="text-[11px] text-muted-foreground">{from}</p>
                </div>
                <div className="flex-1 px-2 relative">
                  <div className="border-t border-dashed border-border relative">
                    <span className="absolute -top-2.5 left-0 text-muted-foreground">
                      <Plane className="h-3 w-3" />
                    </span>
                    <span className="absolute -top-2.5 right-0 text-muted-foreground rotate-180">
                      <Plane className="h-3 w-3" />
                    </span>
                  </div>
                  <p className="text-center text-[11px] text-muted-foreground mt-1 flex items-center justify-center gap-1">
                    <Clock className="h-3 w-3" />
                    {f.dur}
                    {f.stops > 0 && ` · ${f.stops} stop`}
                  </p>
                </div>
                <div>
                  <p className="font-display text-lg font-bold leading-tight">{f.arr}</p>
                  <p className="text-[11px] text-muted-foreground">{to}</p>
                </div>
              </div>
              <Badge variant={f.stops === 0 ? 'success' : 'secondary'} className="text-[10px]">
                {f.stops === 0 ? 'Non-stop' : '1 stop'}
              </Badge>
              <div className="text-right shrink-0">
                <p className="font-display text-xl font-bold text-primary">{f.price}</p>
                <Button
                  size="sm"
                  className="h-8 text-xs mt-1"
                  onClick={() => setExpanded(expanded === f.code ? null : f.code)}
                >
                  Select{' '}
                  {expanded === f.code ? (
                    <ChevronUp className="h-3.5 w-3.5 ml-1" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5 ml-1" />
                  )}
                </Button>
              </div>
            </div>
            {expanded === f.code && (
              <div className="px-5 py-3 border-t border-border bg-muted/30 text-xs text-muted-foreground">
                Fare includes baggage &amp; taxes · Cancellation from Rs 2,000 · Meal available at
                Rs 1,200
              </div>
            )}
          </Card>
        ))}
        {list.length === 0 && (
          <Card className="text-center py-10 text-sm text-muted-foreground">
            No flights match this filter.
          </Card>
        )}
      </div>

      <Card
        padding="sm"
        animate="fade-up"
        className="mt-6 flex items-center gap-3 flex-wrap border-dashed"
      >
        <img
          src={img.travel.plane}
          alt="Plane"
          className="h-10 w-10 rounded-xl object-cover hidden sm:block"
          loading="lazy"
          decoding="async"
        />
        <p className="text-sm text-muted-foreground flex-1 min-w-[200px]">
          <span className="font-semibold text-foreground">Price promise:</span> found a lower fare
          elsewhere within 24 hours? We refund the difference.
        </p>
      </Card>
    </TemplateShell>
  );
}
