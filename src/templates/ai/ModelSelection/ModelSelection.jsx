import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge } from '@/components/ui';
import { models } from './data/mockData';
import { Check } from 'lucide-react';

export default function ModelSelection() {
  const [selected, setSelected] = useState(models[1].id);
  return (
    <TemplateShell title="Model Selection" description="Compare models and pick one." category="AI">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {models.map((m, i) => (
          <Card
            key={m.id}
            animate="fade-up"
            animationDelay={i * 75}
            className={`cursor-pointer transition-all ${selected === m.id ? 'border-primary shadow-md' : 'hover:border-primary/40'}`}
            onClick={() => setSelected(m.id)}
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-display font-semibold">{m.name}</h3>
              {m.popular && <Badge size="sm">Popular</Badge>}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{m.blurb}</p>
            <p className="mt-4 font-display text-xl font-bold">
              ${m.price}
              <span className="text-sm font-normal text-muted-foreground">/1M tok</span>
            </p>
            <ul className="mt-4 space-y-2">
              {m.features.map((f) => (
                <li key={f} className="flex gap-2 text-sm text-muted-foreground">
                  <Check className="h-4 w-4 text-primary shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <Button className="mt-6 w-full" variant={selected === m.id ? 'primary' : 'outline'}>
              {selected === m.id ? 'Selected' : 'Select'}
            </Button>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
