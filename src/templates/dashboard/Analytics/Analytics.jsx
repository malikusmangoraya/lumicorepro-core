import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { metrics, series } from './data/mockData';
import { Download } from 'lucide-react';

export default function Analytics() {
  const max = Math.max(...series.map((s) => s.value));
  return (
    <TemplateShell
      title="Analytics"
      description="Traffic and conversion at a glance."
      category="Dashboard"
      actions={
        <Button size="sm" variant="outline" leftIcon={Download}>
          Export CSV
        </Button>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {metrics.map((m, i) => (
          <Card key={m.label} animate="fade-up" animationDelay={i * 60} className="hover-lift">
            <p className="text-sm text-muted-foreground">{m.label}</p>
            <p className="mt-1 font-display text-2xl font-bold">{m.value}</p>
            <Badge variant="info" size="sm" className="mt-2">
              {m.change}
            </Badge>
          </Card>
        ))}
      </div>
      <Card animate="fade-up" animationDelay={200}>
        <h3 className="font-display font-semibold mb-6">Visitors (7 days)</h3>
        <div className="flex h-48 items-end gap-3">
          {series.map((s) => (
            <div key={s.day} className="flex-1 flex flex-col items-center gap-2">
              <div
                className="w-full rounded-t-lg bg-primary/85 transition-all duration-300 hover:bg-primary hover-glow"
                style={{ height: `${(s.value / max) * 100}%` }}
                title={`${s.value}`}
              />
              <span className="text-xs text-muted-foreground">{s.day}</span>
            </div>
          ))}
        </div>
      </Card>
    </TemplateShell>
  );
}
