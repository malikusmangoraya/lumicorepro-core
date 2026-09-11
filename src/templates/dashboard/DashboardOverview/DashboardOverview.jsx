import { TrendingUp, Users, ShoppingBag, Activity } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, CardContent, Badge, Button, Progress } from '@/components/ui';
import { stats, activity } from './data/mockData';

const icons = { users: Users, revenue: TrendingUp, orders: ShoppingBag, growth: Activity };

export default function DashboardOverview() {
  return (
    <TemplateShell
      title="Dashboard Overview"
      description="Key metrics, activity, and quick actions."
      category="Dashboard"
      actions={<Button size="sm">Export</Button>}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => {
          const Icon = icons[s.key];
          return (
            <Card
              key={s.key}
              animate="fade-up"
              animationDelay={i * 75}
              className="hover-lift"
              padding="md"
            >
              <CardContent className="flex items-start justify-between gap-3 p-0">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="mt-1 font-display text-2xl font-bold">{s.value}</p>
                  <Badge
                    variant={s.delta.startsWith('+') ? 'success' : 'danger'}
                    size="sm"
                    className="mt-2"
                  >
                    {s.delta}
                  </Badge>
                </div>
                <div className="rounded-lg bg-primary/10 p-2 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2" animate="fade-up" animationDelay={200}>
          <h3 className="font-display font-semibold mb-4">Revenue pace</h3>
          <Progress value={72} showLabel label="Monthly goal" />
          <div className="mt-6 flex h-32 items-end gap-2">
            {[40, 55, 48, 70, 62, 80, 74, 88, 76, 92, 85, 96].map((h, i) => (
              <div
                key={i}
                className="flex-1 rounded-t bg-primary/80 transition-all hover:bg-primary"
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </Card>
        <Card animate="fade-up" animationDelay={250}>
          <h3 className="font-display font-semibold mb-4">Activity</h3>
          <ul className="space-y-3">
            {activity.map((a) => (
              <li key={a.id} className="flex gap-3 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                <div>
                  <p className="text-foreground">{a.text}</p>
                  <p className="text-xs text-muted-foreground">{a.time}</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </TemplateShell>
  );
}
