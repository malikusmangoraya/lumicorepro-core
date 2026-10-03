/**
 * ToastRegion — the global surface for app notifications.
 *
 * AppContext already produced notifications (login, logout, 2FA hints) but nothing
 * rendered them, and React Query errors had nowhere to go. This renders both:
 * `registerNotificationHandler` lets non-React code (the QueryCache `onError`)
 * push into the same list.
 */
import { useEffect } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import { registerNotificationHandler } from '../../services/notificationBus';
import { cn, getAnimationClass } from '../../utils';

const TONES = {
  success: { Icon: CheckCircle2, icon: 'text-emerald-500' },
  error: { Icon: XCircle, icon: 'text-destructive' },
  warning: { Icon: AlertTriangle, icon: 'text-amber-500' },
  info: { Icon: Info, icon: 'text-primary' },
};

export default function ToastRegion() {
  const { notifications, addNotification, dismissNotification } = useNotifications();

  useEffect(
    () => registerNotificationHandler((message, type) => addNotification(message, type)),
    [addNotification]
  );

  if (!notifications?.length) return null;

  return (
    <div
      className="toast-container fixed bottom-4 right-4 z-[100] flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {notifications.map((n) => {
        const { Icon, icon } = TONES[n.type] || TONES.info;
        return (
          <div
            key={n.id}
            role={n.type === 'error' ? 'alert' : 'status'}
            className={cn(
              'flex items-start gap-3 rounded-xl border border-border bg-card p-3 text-card-foreground shadow-lg',
              getAnimationClass('fade-up')
            )}
          >
            <Icon className={cn('mt-0.5 h-4 w-4 shrink-0', icon)} aria-hidden="true" />
            <p className="flex-1 text-sm">{n.message}</p>
            <button
              type="button"
              onClick={() => dismissNotification?.(n.id)}
              className="shrink-0 rounded-lg p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Dismiss notification"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
