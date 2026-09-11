import { useState } from 'react';
import { Check, X, Sparkles, Rocket, ShieldCheck, ArrowRight } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { services, process } from './data/mockData';

export default function ServicesOffering() {
  const [service, setService] = useState(services[1]);

  return (
    <TemplateShell
      title="Services & Rates"
      description="Fixed scope, fixed price, and a process you can follow in real time."
      category="Portfolio"
      actions={
        <Button size="sm">
          <Rocket className="h-4 w-4 mr-1" />
          Start a Project
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {services.map((s, i) => {
          const active = service?.name === s.name;
          return (
            <Card
              key={s.name}
              animate="fade-up"
              animationDelay={i * 80}
              onClick={() => setService(s)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') setService(s);
              }}
              className={cn(
                'flex flex-col cursor-pointer transition-all relative',
                active && 'border-primary shadow-glow-lg md:-translate-y-2'
              )}
            >
              {s.popular && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                  {'★'} Most Requested
                </Badge>
              )}
              <p className="font-display font-semibold text-sm text-muted-foreground">{s.name}</p>
              <div className="flex items-baseline gap-1 my-2">
                <span className="font-display text-3xl font-bold">{s.price}</span>
              </div>
              <p className="text-xs text-muted-foreground mb-5">{s.tagline}</p>
              <ul className="space-y-2.5 mb-6 flex-1">
                {s.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
              <Button variant={active ? 'primary' : 'outline'} className="w-full">
                Request Quote
              </Button>
            </Card>
          );
        })}
      </div>

      {/* Process */}
      <h3 className="font-display text-lg font-bold mb-4">How It Works</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {process.map((p, i) => (
          <Card
            key={p.step}
            animate="fade-up"
            animationDelay={i * 70}
            padding="sm"
            className="relative overflow-hidden"
          >
            <span className="absolute -right-2 -top-3 font-display text-6xl font-black text-muted-foreground/10 select-none">
              {p.step}
            </span>
            <p className="font-display text-sm font-bold text-primary">
              {p.step} — {p.title}
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed mt-2">{p.desc}</p>
          </Card>
        ))}
      </div>

      {/* Selected service summary */}
      <Card
        animate="fade-up"
        padding="sm"
        className="border-dashed flex flex-wrap items-center gap-4"
      >
        <ShieldCheck className="h-6 w-6 text-emerald-400 shrink-0" />
        <div className="flex-1 min-w-[200px]">
          <p className="text-sm font-semibold">
            {service.name} — {service.price}
          </p>
          <p className="text-xs text-muted-foreground">
            Milestone payments · 7-day free ramp · IP fully yours
          </p>
        </div>
        <Button size="sm">
          <ArrowRight className="h-4 w-4 mr-1" />
          Book a Free Call
        </Button>
      </Card>
    </TemplateShell>
  );
}
