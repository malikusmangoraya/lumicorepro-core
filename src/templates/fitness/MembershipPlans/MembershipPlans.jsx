import { Check, X, Sparkles, ShieldCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { plans, guarantees } from './data/mockData';

export default function MembershipPlans() {
  return (
    <TemplateShell
      title="Membership Plans"
      description="Simple, honest pricing. No contracts, no hidden fees."
      category="Fitness"
      actions={
        <Badge variant="success">
          <Sparkles className="h-3 w-3 mr-1" />
          First class is free
        </Badge>
      }
    >
      {/* Guarantee strip */}
      <Card animate="fade-up" padding="sm" className="flex flex-wrap gap-3 items-center mb-8">
        {guarantees.map((g) => (
          <span key={g} className="flex items-center gap-1.5 text-xs font-medium">
            <Check className="h-3.5 w-3.5 text-emerald-400" />
            {g}
          </span>
        ))}
        <Button size="sm" variant="outline" className="ml-auto h-8 text-xs">
          <ShieldCheck className="h-3.5 w-3.5 mr-1" />
          Payment Secure
        </Button>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((p, i) => (
          <Card
            key={p.name}
            animate="fade-up"
            animationDelay={i * 90}
            className={cn(
              'flex flex-col relative',
              p.popular && 'border-primary shadow-glow-lg md:-translate-y-2'
            )}
          >
            {p.popular && (
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                {'★'} Most Popular
              </Badge>
            )}
            <p className="font-display font-semibold text-sm text-muted-foreground">{p.name}</p>
            <div className="flex items-baseline gap-1 my-2">
              <span className="font-display text-4xl font-bold">
                Rs {p.price.replace(/,/g, '')}
              </span>
              <span className="text-xs text-muted-foreground">
                /{p.name === 'Day Pass' ? 'day' : p.name === 'Monthly' ? 'month' : 'year'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mb-5">{p.tagline}</p>
            <ul className="space-y-2.5 mb-6 flex-1">
              {p.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  {f}
                </li>
              ))}
              {!p.all &&
                [1, 2].map((_, j) => (
                  <li
                    key={`empty-${j}`}
                    className="flex items-start gap-2 text-sm text-muted-foreground/40"
                  >
                    <X className="h-4 w-4 shrink-0 mt-0.5" />
                    Locked feature in higher plans
                  </li>
                ))}
            </ul>
            <Button className="w-full" size="lg" variant={p.popular ? 'primary' : 'outline'}>
              Choose {p.name}
            </Button>
          </Card>
        ))}
      </div>

      <p className="text-center text-xs text-muted-foreground mt-6">
        Prices in PKR, inclusive of all taxes. Student & family discounts available at the front
        desk.
      </p>
    </TemplateShell>
  );
}
