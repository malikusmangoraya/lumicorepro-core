import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { orders, filters } from './data/mockData';

export default function OrdersHistory() {
  const [filter, setFilter] = useState('all');
  const list = orders.filter((o) => filter === 'all' || o.status === filter);
  const tone = { delivered: 'success', shipped: 'info', pending: 'warning', cancelled: 'danger' };
  return (
    <TemplateShell
      title="Orders History"
      description="Track and revisit past orders."
      category="E-Commerce"
    >
      <div className="flex flex-wrap gap-2 mb-4">
        {filters.map((f) => (
          <Button
            key={f.id}
            size="sm"
            variant={filter === f.id ? 'primary' : 'outline'}
            onClick={() => setFilter(f.id)}
          >
            {f.label}
          </Button>
        ))}
      </div>
      <div className="space-y-3">
        {list.map((o, i) => (
          <Card
            key={o.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover-lift"
            animate="fade-up"
            animationDelay={i * 50}
          >
            <div>
              <p className="font-medium">{o.id}</p>
              <p className="text-sm text-muted-foreground">
                {o.date} · {o.items} items
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={tone[o.status]}>{o.status}</Badge>
              <span className="font-semibold">${o.total}</span>
              <Button size="sm" variant="ghost">
                Details
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
