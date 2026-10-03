import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Package, CreditCard, Bell, Loader2, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { dashboardAPI } from '../services/api';

const USAGE_KEYS = [
  { key: 'ai_generation', label: 'AI Generation' },
  { key: 'ai_chat', label: 'AI Chat' },
  { key: 'api', label: 'API Calls' },
];

export default function Dashboard() {
  const { t } = useTranslation();
  const { data: meData, isLoading: meLoading, error: meError } = useQuery({
    queryKey: ['dashboard', 'me'],
    queryFn: () => dashboardAPI.me(),
  });

  const { data: chartsData } = useQuery({
    queryKey: ['dashboard', 'charts'],
    queryFn: () => dashboardAPI.myCharts(6),
  });

  if (meLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (meError) {
    return (
      <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{t('dashboard.loadError', 'Failed to load dashboard data')}</span>
      </div>
    );
  }

  const me = meData?.data?.data || {};
  const orders = me.orders || {};
  const subscription = me.subscription || {};
  const usage = me.usage || {};
  const limits = usage.limits || {};
  const used = usage.used || {};
  const charts = chartsData?.data?.data || [];

  const fmt = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">{t('dashboard.title', 'My Dashboard')}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Package className="w-5 h-5 text-primary" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">{t('dashboard.myOrders', 'My Orders')}</span>
          </div>
          <p className="text-3xl font-bold text-foreground">{orders.total || 0}</p>
          <p className="text-sm text-muted-foreground mt-1">{t('dashboard.totalSpent', 'Total spent')}: {fmt(orders.spent)}</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-primary" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">{t('dashboard.subscription', 'Subscription')}</span>
          </div>
          <p className="text-3xl font-bold text-foreground">{subscription.plan || t('dashboard.free', 'Free')}</p>
          <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium ${
            subscription.active
              ? 'bg-green-500/10 text-green-600 dark:text-green-400'
              : 'bg-red-500/10 text-red-600 dark:text-red-400'
          }`}>
            {subscription.active ? t('dashboard.active', 'Active') : t('dashboard.inactive', 'Inactive')}
          </span>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Bell className="w-5 h-5 text-primary" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">{t('dashboard.notifications', 'Notifications')}</span>
          </div>
          <p className="text-3xl font-bold text-foreground">{me.unreadNotifications || 0}</p>
          <p className="text-sm text-muted-foreground mt-1">{t('dashboard.unread', 'Unread')}</p>
        </div>
      </div>

      {USAGE_KEYS.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-lg font-semibold text-foreground mb-4">{t('dashboard.usageTitle', 'Usage This Month')}</h2>
          <div className="space-y-4">
            {USAGE_KEYS.map(({ key, label }) => {
              const u = used[key] || 0;
              const l = limits[key] || 0;
              const pct = l > 0 ? Math.min((u / l) * 100, 100) : 0;
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-foreground font-medium">{t(`dashboard.usage.${key}`, label)}</span>
                    <span className="text-muted-foreground">{u} / {l}</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {charts.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-lg font-semibold text-foreground mb-4">{t('dashboard.monthlyActivity', 'Monthly Activity')}</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e5e7eb)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground, #6b7280)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground, #6b7280)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--color-card, #ffffff)',
                    border: '1px solid var(--color-border, #e5e7eb)',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="orders"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name={t('dashboard.orders', 'Orders')}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name={t('dashboard.revenue', 'Revenue')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
