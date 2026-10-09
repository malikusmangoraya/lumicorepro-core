import { TrendingUp, Users, ShoppingBag, Activity, ArrowUpRight, ArrowDownRight, Target, Clock } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, CardContent, Badge, Button, Progress, StatsCard, ScrollReveal, StaggerContainer, GlassButton } from '@/components/ui';
import { stats, activity, revenueData, topProducts } from './data/mockData';
import { cn } from '@/utils';

const icons = { users: Users, revenue: TrendingUp, orders: ShoppingBag, growth: Activity };

export default function DashboardOverview() {
  return (
    <TemplateShell
      title="Dashboard Overview"
      description="Key metrics, activity, and quick actions."
      category="Dashboard"
      actions={
        <div className="flex gap-2">
          <GlassButton variant="outline" size="sm" leftIcon={<Clock className="h-4 w-4" />}>
            Last 7 days
          </GlassButton>
          <GlassButton variant="primary" size="sm" leftIcon={<ArrowUpRight className="h-4 w-4" />}>
            Export Report
          </GlassButton>
        </div>
      }
    >
      {/* Stats Grid */}
      <ScrollReveal animate="fade-up">
        <StaggerContainer stagger={0.08}>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((s, i) => {
              const Icon = icons[s.key];
              const isPositive = s.delta.startsWith('+');
              return (
                <ScrollReveal key={s.key} animate="none">
                  <StatsCard
                    title={s.label}
                    value={s.value}
                    change={parseFloat(s.delta.replace(/[+%]/g, ''))}
                    changeLabel={isPositive ? 'vs last period' : 'vs last period'}
                    trend={isPositive ? 'up' : 'down'}
                    icon={Icon}
                    iconColor={s.key === 'revenue' ? 'primary' : s.key === 'users' ? 'emerald' : s.key === 'orders' ? 'amber' : 'violet'}
                  />
                </ScrollReveal>
              );
            })}
          </div>
        </StaggerContainer>
      </ScrollReveal>

      {/* Main Charts & Activity */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ScrollReveal animate="fade-up" delay={0.1}>
          <Card className="lg:col-span-2" padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-display text-lg font-semibold">Revenue Overview</h3>
              <div className="flex items-center gap-2">
                <Badge variant="success" size="sm" className="gap-1">
                  <ArrowUpRight className="h-3 w-3" />
                  +12.5%
                </Badge>
              </div>
            </div>
            <div className="relative h-64">
              <svg className="w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="revenueStroke" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="hsl(var(--primary))" />
                    <stop offset="100%" stopColor="hsl(var(--cyan))" />
                  </linearGradient>
                </defs>
                <rect width="400" height="200" fill="url(#revenueGradient)" />
                <path
                  d="M20,160 C80,120 140,140 200,100 C260,60 320,80 380,50"
                  stroke="url(#revenueStroke)"
                  strokeWidth="3"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter="drop-shadow(0 4px 8px rgba(13, 148, 136, 0.3))"
                />
                {revenueData.map((point, i) => (
                  <circle
                    key={i}
                    cx={20 + (i / (revenueData.length - 1)) * 360}
                    cy={160 - (point.value / 100) * 120}
                    r="5"
                    fill="hsl(var(--primary))"
                    stroke="white"
                    strokeWidth="2"
                    filter="drop-shadow(0 2px 4px rgba(13, 148, 136, 0.4))"
                  />
                ))}
              </svg>
            </div>
            <div className="mt-6 flex items-center justify-between text-sm text-muted-foreground">
              <span>Jan</span>
              <span>Feb</span>
              <span>Mar</span>
              <span>Apr</span>
              <span>May</span>
              <span>Jun</span>
              <span>Jul</span>
              <span>Aug</span>
              <span>Sep</span>
              <span>Oct</span>
              <span>Nov</span>
              <span>Dec</span>
            </div>
          </Card>
        </ScrollReveal>

        <ScrollReveal animate="fade-up" delay={0.15}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold">Monthly Goal</h3>
              <Target className="h-5 w-5 text-primary" />
            </div>
            <Progress value={72} showLabel label="Revenue target" className="mb-6" />
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    <TrendingUp className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Projected Revenue</p>
                    <p className="text-xs text-muted-foreground">Based on current pace</p>
                  </div>
                </div>
                <span className="font-display font-bold text-primary">$98.4K</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald/10 text-emerald">
                    <Users className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">New Customers</p>
                    <p className="text-xs text-muted-foreground">This month</p>
                  </div>
                </div>
                <span className="font-display font-bold text-emerald">1,234</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber/10 text-amber">
                    <ShoppingBag className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Conversion Rate</p>
                    <p className="text-xs text-muted-foreground">Overall average</p>
                  </div>
                </div>
                <span className="font-display font-bold text-amber">3.2%</span>
              </div>
            </div>
          </Card>
        </ScrollReveal>
      </div>

      {/* Top Products & Recent Activity */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ScrollReveal animate="fade-up" delay={0.2}>
          <Card padding="lg">
            <h3 className="font-display font-semibold mb-4">Top Products</h3>
            <div className="space-y-4">
              {topProducts.map((product, i) => (
                <div
                  key={product.id}
                  className={cn(
                    'flex items-center gap-4 p-3 rounded-lg transition-colors',
                    'hover:bg-muted/50'
                  )}
                >
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{product.name}</p>
                    <p className="text-xs text-muted-foreground">{product.category}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-display font-bold">${product.revenue}</p>
                    <Badge variant="success" size="sm" className="mt-1">
                      {product.growth}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </ScrollReveal>

        <ScrollReveal animate="fade-up" delay={0.25}>
          <Card padding="lg">
            <h3 className="font-display font-semibold mb-4">Recent Activity</h3>
            <ul className="space-y-3">
              {activity.map((a) => (
                <li key={a.id} className="flex gap-3 text-sm">
                  <div className={cn(
                    'mt-1.5 h-1.5 w-1.5 rounded-full shrink-0',
                    a.type === 'order' && 'bg-primary',
                    a.type === 'user' && 'bg-emerald',
                    a.type === 'alert' && 'bg-amber',
                    a.type === 'system' && 'bg-violet',
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground truncate">{a.text}</p>
                    <p className="text-xs text-muted-foreground">{a.time}</p>
                  </div>
                </li>
              ))}
            </ul>
            <GlassButton variant="outline" size="sm" fullWidth className="mt-4" leftIcon={<Clock className="h-4 w-4" />}>
              View All Activity
            </GlassButton>
          </Card>
        </ScrollReveal>
      </div>
    </TemplateShell>
  );
}