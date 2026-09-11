import { Phone, Mail, Pin, TrendingUp, BadgeCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { cn } from '@/utils';
import { agents, stats } from './data/mockData';

const COLORS = [
  'from-primary to-indigo-600',
  'from-emerald-500 to-teal-600',
  'from-amber-500 to-orange-600',
  'from-violet-500 to-purple-600',
  'from-rose-500 to-pink-600',
  'from-sky-500 to-blue-600',
];

function initials(name) {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export default function AgentDirectory() {
  return (
    <TemplateShell
      title="Realty — Agent Directory"
      description="Hand-picked consultants across Karachi & Lahore, vetted by closed deals."
      category="Real Estate"
      actions={
        <Button size="sm">
          <BadgeCheck className="h-4 w-4 mr-1" />
          Become an Agent
        </Button>
      }
    >
      {/* Stats strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {stats.map((s, i) => (
          <Card key={s.label} animate="fade-up" animationDelay={i * 60} padding="sm">
            <p className="font-display text-xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Agent cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {agents.map((a, i) => (
          <Card
            key={a.name}
            animate="fade-up"
            animationDelay={(i * 70) % 350}
            className="flex flex-col"
          >
            <div className="flex items-start gap-4 mb-4">
              <Avatar className="h-14 w-14">
                <div
                  className={cn(
                    'h-full w-full flex items-center justify-center text-white font-display font-bold bg-gradient-to-br',
                    COLORS[i % COLORS.length]
                  )}
                >
                  {initials(a.name)}
                </div>
              </Avatar>
              <div className="min-w-0">
                <h3 className="font-display font-semibold leading-snug">{a.name}</h3>
                <p className="text-xs text-muted-foreground">{a.role}</p>
                <p className="flex items-center gap-1 text-xs mt-1">
                  <Pin className="h-3 w-3 text-primary" />
                  {a.area}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="rounded-xl bg-muted/60 p-2 text-center">
                <p className="text-[11px] text-muted-foreground">Deals</p>
                <p className="text-sm font-bold">{a.deals}</p>
              </div>
              <div className="rounded-xl bg-muted/60 p-2 text-center">
                <p className="text-[11px] text-muted-foreground">Rating</p>
                <p className="text-sm font-bold text-amber-400">★ {a.rating}</p>
              </div>
              <div className="rounded-xl bg-muted/60 p-2 text-center">
                <p className="text-[11px] text-muted-foreground">Sales</p>
                <p className="text-sm font-bold">{a.sales}</p>
              </div>
            </div>
            <div className="mt-auto flex items-center justify-between gap-2 pt-3 border-t border-border/60">
              <Badge variant="outline" className="text-[10px]">
                <TrendingUp className="h-3 w-3 mr-1" />
                {a.specialty}
              </Badge>
              <div className="flex gap-1.5">
                <Button size="sm" className="h-8 w-8 p-0" aria-label={`Call ${a.name}`}>
                  <Phone className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 w-8 p-0"
                  aria-label={`Email ${a.name}`}
                >
                  <Mail className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
