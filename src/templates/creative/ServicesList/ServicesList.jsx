import { Palette, Monitor, Camera, Clapperboard, Check, ArrowRight } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { services, process } from './data/mockData';

const SERVICE_ICONS = { Palette, Monitor, Camera, Clapperboard };

export default function ServicesList() {
  return (
    <TemplateShell
      title="What We Craft"
      description="Four disciplines, one studio, no hand-off gaps between them."
      category="Creative"
      actions={
        <Button size="sm">
          <ArrowRight className="h-4 w-4 mr-1" />
          Request a Quote
        </Button>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-10">
        {services.map((s, i) => {
          const Icon = SERVICE_ICONS[s.icon];
          return (
            <Card
              key={s.name}
              animate="fade-up"
              animationDelay={(i * 70) % 300}
              className="hover-lift"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-pink-500/20 to-rose-500/10 flex items-center justify-center shrink-0">
                  <Icon className="h-6 w-6 text-rose-400" />
                </div>
                <div>
                  <h3 className="font-display text-lg font-bold">{s.name}</h3>
                  <p className="text-sm font-bold text-primary">{s.price}</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed mb-4">{s.desc}</p>
              <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border/60">
                <Badge variant="outline" size="sm" className="text-[10px]">
                  <Check className="h-3 w-3 text-emerald-400 mr-1" />
                  {s.includes}
                </Badge>
                <Button size="sm" variant="ghost" className="ml-auto h-8 text-xs text-primary">
                  View Sample <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Process */}
      <h3 className="font-display text-lg font-bold mb-4">Our Studio Rhythm</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {process.map((p, i) => (
          <Card key={p.step} animate="fade-up" animationDelay={i * 60} padding="sm">
            <p className="font-display text-sm font-bold text-rose-400 mb-1">{p.step}</p>
            <p className="text-xs text-muted-foreground leading-relaxed">{p.desc}</p>
          </Card>
        ))}
      </div>

      <Card
        padding="sm"
        animate="fade-up"
        className="border-dashed flex flex-wrap items-center gap-3"
      >
        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <Palette className="h-5 w-5 text-primary" />
        </div>
        <p className="text-sm text-muted-foreground flex-1 min-w-[220px]">
          <span className="font-semibold text-foreground">Not sure what you need?</span> Book a free
          30-minute direction call — we'll point you right, even if it's not us.
        </p>
        <Button size="sm">Book Direction Call</Button>
      </Card>
    </TemplateShell>
  );
}
