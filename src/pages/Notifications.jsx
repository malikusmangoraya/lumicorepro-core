import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../components/common/ThemeProvider';
import { notificationsAPI } from '../services/api';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Loader2,
} from 'lucide-react';

const TABS = [
  { key: 'all', label: 'All' },
  { key: 'unread', label: 'Unread' },
];

const NOTIFICATION_ICONS = {
  success: CheckCircle2,
  warning: AlertTriangle,
  info: MessageSquare,
};

function timeAgo(dateStr) {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function Notifications() {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [tab, setTab] = useState('all');

  const readFilter = tab === 'unread' ? false : undefined;

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['notifications', { page, read: readFilter }],
    queryFn: () => notificationsAPI.getAll({ page, limit: 15, read: readFilter }),
  });

  const notifications = data?.data?.data ?? [];
  const pagination = data?.data?.pagination ?? { totalPages: 1, page: 1, total: 0 };

  const markAllMutation = useMutation({
    mutationFn: () => notificationsAPI.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id) => notificationsAPI.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  return (
    <div className="min-h-screen bg-background px-4 py-8 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-card rounded-xl border border-border shadow-sm">
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-foreground">
                {t('notifications.title', 'Notifications')}
              </h1>
              {isFetching && (
                <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" aria-hidden="true" />
              )}
            </div>
            <button
              onClick={() => markAllMutation.mutate()}
              disabled={markAllMutation.isPending}
              className="text-sm text-primary hover:underline disabled:opacity-50 flex items-center gap-1"
            >
              <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
              {t('notifications.markAllRead', 'Mark all read')}
            </button>
          </div>

          <div className="flex gap-2 px-6 pt-4">
            {TABS.map((t_) => (
              <button
                key={t_.key}
                onClick={() => { setTab(t_.key); setPage(1); }}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  tab === t_.key
                    ? 'bg-primary text-white'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {t_.label}
              </button>
            ))}
          </div>

          <div className="divide-y divide-border mt-2">
            {isLoading && (
              <div className="px-6 py-4 space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-start gap-3 animate-pulse">
                    <div className="h-8 w-8 rounded-full bg-muted" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-muted rounded w-1/3" />
                      <div className="h-3 bg-muted rounded w-2/3" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!isLoading && notifications.length === 0 && (
              <div className="px-6 py-12 text-center">
                <AlertCircle className="h-10 w-10 text-muted-foreground mx-auto mb-3" aria-hidden="true" />
                <p className="text-sm text-muted-foreground">
                  {t('notifications.empty', 'No notifications found')}
                </p>
              </div>
            )}

            {!isLoading &&
              notifications.map((item) => {
                const Icon = NOTIFICATION_ICONS[item.type] || Bell;
                const iconColor =
                  item.type === 'success'
                    ? 'text-green-500'
                    : item.type === 'warning'
                      ? 'text-yellow-500'
                      : 'text-primary';

                return (
                  <div
                    key={item.id}
                    className={`flex items-start gap-3 px-6 py-4 ${
                      !item.read ? 'bg-primary/10' : ''
                    }`}
                  >
                    <span className={`mt-0.5 flex-shrink-0 ${iconColor}`}>
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground">
                        {item.title}
                      </p>
                      <p className="text-sm text-muted-foreground line-clamp-2 mt-0.5">
                        {item.message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {timeAgo(item.createdAt)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {!item.read && (
                        <button
                          onClick={() => markReadMutation.mutate(item.id)}
                          className="text-xs text-primary hover:underline whitespace-nowrap"
                        >
                          {t('notifications.markRead', 'Mark read')}
                        </button>
                      )}
                      {item.link && (
                        <a
                          href={item.link}
                          className="text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <ChevronRight className="h-4 w-4" aria-hidden="true" />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>

          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-border">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                {t('common.prev', 'Prev')}
              </button>
              <span className="text-sm text-muted-foreground">
                {t('common.page', 'Page')} {pagination.page} / {pagination.totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(pagination.totalPages, p + 1))}
                disabled={page >= pagination.totalPages}
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {t('common.next', 'Next')}
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
