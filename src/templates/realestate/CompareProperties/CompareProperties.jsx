import { Gem, House, Building2, ShieldCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { properties, compareRows } from './data/mockData';

const TYPE_ICONS = { Villa: House, Duplex: Building2, Apartment: Building2 };

export default function CompareProperties() {
  return (
    <TemplateShell
      title="Compare Properties"
      description="Side-by-side breakdown across price, area, and layout — pick with data, not impulse."
      category="Real Estate"
      actions={
        <Button size="sm">
          <Gem className="h-4 w-4 mr-1" />
          Shortlist a Property
        </Button>
      }
    >
      <Card animate="fade-up" className="overflow-hidden">
        {/* Header row */}
        <div className="grid grid-cols-[110px_1fr_1fr_1fr] sm:grid-cols-[160px_1fr_1fr_1fr]">
          <div className="p-4 sm:p-5 bg-muted/50 border-b border-border" />
          {properties.map((p, i) => {
            const Icon = TYPE_ICONS[p.type] || Home;
            return (
              <div
                key={p.name}
                className="p-4 sm:p-5 bg-muted/50 border-b border-border flex flex-col items-center sm:items-start relative"
              >
                {p.posh && (
                  <Badge className="absolute top-2 right-2 hidden sm:inline-flex">
                    <Gem className="h-3 w-3 mr-1" />
                    Premium
                  </Badge>
                )}
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-2">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <p className="font-display font-semibold text-sm leading-snug text-center sm:text-left">
                  {p.name}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {p.type} · {p.location}
                </p>
                <p className="font-display text-lg font-bold text-primary mt-2">{p.price}</p>
              </div>
            );
          })}
        </div>

        {/* Rows */}
        {compareRows.map((row) => (
          <div
            key={row.label}
            className="grid grid-cols-[110px_1fr_1fr_1fr] sm:grid-cols-[160px_1fr_1fr_1fr] border-b border-border/60 last:border-b-0"
          >
            <div className="p-4 sm:p-5 text-sm font-medium text-muted-foreground bg-muted/50">
              {row.label}
            </div>
            {properties.map((p) => (
              <div key={p.name + row.key} className="p-4 sm:p-5 text-sm text-foreground">
                {String(p[row.key])}
              </div>
            ))}
          </div>
        ))}
      </Card>

      {/* Verdict */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
        {properties.map((p, i) => (
          <Card
            key={p.name + 'verdict'}
            animate="fade-up"
            animationDelay={i * 80}
            padding="sm"
            className={i === 0 ? 'border-primary shadow-glow-sm' : ''}
          >
            <div className="flex items-center gap-2 mb-2">
              <House className="h-4 w-4 text-primary" />
              <p className="font-display font-semibold text-sm">{p.name}</p>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {p.posh
                ? 'Premium community with the most space per room and strongest resale outlook.'
                : 'Best value per square foot — ideal for a growing family on a single plot.'}
            </p>
            {i === 0 && (
              <Badge variant="success" className="mt-3 text-[10px]">
                <ShieldCheck className="h-3 w-3 mr-1" />
                Our Top Pick for Value
              </Badge>
            )}
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
