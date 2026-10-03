import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useTheme } from './ThemeProvider';
import { notificationsAPI } from '../../services/api';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  MessageSquare,
} from 'lucide-react';

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

export default function NotificationBell() {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsAPI.getAll({ limit: 10 }),
    refetchInterval: 30000,
  });

  const notifications = data?.data?.data ?? [];
  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllMutation = useMutation({
    mutationFn: () => notificationsAPI.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  useEffect(() => {
    function handleMousedown(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleMousedown);
    return () => document.removeEventListener('mousedown', handleMousedown);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        aria-label={t('notifications.label', 'Notifications')}
        aria-expanded={open}
        className="relative p-2 rounded-lg hover:bg-muted transition-colors"
      >
        <Bell className="h-5 w-5 text-foreground" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-destructive text-white rounded-full text-xs min-w-[18px] h-[18px] flex items-center justify-center px-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className={`absolute right-0 top-full mt-2 w-80 max-h-80 overflow-y-auto rounded-xl border shadow-lg z-50 ${
            isDark ? 'bg-card border-border' : 'bg-card border-border'
          }`}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground">
              {t('notifications.title', 'Notifications')}
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
                className="text-xs text-primary hover:underline disabled:opacity-50"
              >
                {t('notifications.markAllRead', 'Mark all read')}
              </button>
            )}
          </div>

          <div className="divide-y divide-border">
            {notifications.length === 0 && (
              <p className="px-4 py-6 text-sm text-muted-foreground text-center">
                {t('notifications.empty', 'No notifications')}
              </p>
            )}

            {notifications.map((item) => {
              const Icon = NOTIFICATION_ICONS[item.type] || Bell;
              const content = (
                <div
                  key={item.id}
                  className={`flex items-start gap-3 px-4 py-3 transition-colors ${
                    !item.read
                      ? isDark
                        ? 'bg-primary/10'
                        : 'bg-primary/10'
                      : 'hover:bg-muted'
                  }`}
                >
                  <span className={`mt-0.5 ${
                    item.type === 'success'
                      ? 'text-green-500'
                      : item.type === 'warning'
                        ? 'text-yellow-500'
                        : 'text-primary'
                  }`}>
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {item.title}
                    </p>
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                      {item.message}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {timeAgo(item.createdAt)}
                    </p>
                  </div>
                </div>
              );

              return item.link ? (
                <a key={item.id} href={item.link} className="block">
                  {content}
                </a>
              ) : (
                <div key={item.id}>{content}</div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
