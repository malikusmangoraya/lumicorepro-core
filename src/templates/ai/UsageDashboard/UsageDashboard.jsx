import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { metrics, usage } from './data/mockData';

export default function UsageDashboard() {
  return (
    <TemplateShell
      title="Usage Dashboard"
      description="Tokens, requests, and plan limits."
      category="AI"
      actions={<Button size="sm">Upgrade</Button>}
    >
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {metrics.map((m, i) => (
          <Card key={m.label} animate="fade-up" animationDelay={i * 60} className="hover-lift">
            <p className="text-sm text-muted-foreground">{m.label}</p>
            <p className="mt-1 font-display text-2xl font-bold">{m.value}</p>
            <Badge size="sm" variant="secondary" className="mt-2">
              {m.hint}
            </Badge>
          </Card>
        ))}
      </div>
      <Card animate="fade-up" animationDelay={150}>
        <h3 className="font-display font-semibold mb-4">Monthly allowance</h3>
        <Progress
          value={usage.percent}
          showLabel
          label={`${usage.used.toLocaleString()} / ${usage.limit.toLocaleString()} tokens`}
        />
      </Card>
    </TemplateShell>
  );
}
