import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { TrendingUp, Package, Users, BarChart3, Loader2, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { dashboardAPI } from '../services/api';

const fmt = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

export default function AdminDashboard() {
  const { t } = useTranslation();

  const { data: statsData, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => dashboardAPI.stats(),
  });

  const { data: revenueData } = useQuery({
    queryKey: ['admin', 'charts', 'revenue'],
    queryFn: () => dashboardAPI.charts('revenue'),
  });

  const { data: usersData } = useQuery({
    queryKey: ['admin', 'charts', 'users'],
    queryFn: () => dashboardAPI.charts('users'),
  });

  const { data: activityData } = useQuery({
    queryKey: ['admin', 'recentActivity'],
    queryFn: () => dashboardAPI.recentActivity(5),
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{t('admin.statsError', 'Failed to load admin stats')}</span>
      </div>
    );
  }

  const stats = statsData?.data?.data || {};
  const revenue = revenueData?.data?.data || [];
  const users = usersData?.data?.data || [];
  const activity = activityData?.data?.data || [];

  const kpis = [
    { label: t('admin.revenue', 'Revenue'), value: fmt(stats.totalRevenue), icon: TrendingUp },
    { label: t('admin.orders', 'Orders'), value: stats.totalOrders || 0, icon: Package },
    { label: t('admin.users', 'Users'), value: stats.totalUsers || 0, icon: Users },
    { label: t('admin.conversion', 'Conversion Rate'), value: `${stats.conversionRate || 0}%`, icon: BarChart3 },
  ];

  const chartTooltipStyle = {
    backgroundColor: 'var(--color-card, #ffffff)',
    border: '1px solid var(--color-border, #e5e7eb)',
    borderRadius: '8px',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">{t('admin.title', 'Admin Dashboard')}</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-card border border-border rounded-lg p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Icon className="w-5 h-5 text-primary" />
              </div>
              <span className="text-sm font-medium text-muted-foreground">{label}</span>
            </div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-lg font-semibold text-foreground mb-4">{t('admin.revenueTrend', 'Revenue Trend')}</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={revenue}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e5e7eb)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground, #6b7280)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground, #6b7280)" />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name={t('admin.revenue', 'Revenue')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-lg font-semibold text-foreground mb-4">{t('admin.userGrowth', 'User Growth')}</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={users}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e5e7eb)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground, #6b7280)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--color-muted-foreground, #6b7280)" />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="users"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name={t('admin.users', 'Users')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="text-lg font-semibold text-foreground mb-4">{t('admin.recentActivity', 'Recent Activity')}</h2>
        {activity.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('admin.noActivity', 'No recent activity')}</p>
        ) : (
          <div className="space-y-3">
            {activity.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                <div className="w-2 h-2 mt-2 rounded-full bg-primary shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{item.title}</p>
                  {item.detail && (
                    <p className="text-xs text-muted-foreground mt-0.5">{item.detail}</p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(item.timestamp))}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
