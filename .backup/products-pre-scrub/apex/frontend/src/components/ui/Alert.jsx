import React from 'react';
import { AlertCircle, CheckCircle2, XCircle, Info, X } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const variants = {
  info: {
    container:
      'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-400',
    icon: 'text-blue-500',
    Icon: Info,
  },
  success: {
    container:
      'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/30 dark:border-green-800 dark:text-green-400',
    icon: 'text-green-500',
    Icon: CheckCircle2,
  },
  warning: {
    container:
      'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/30 dark:border-yellow-800 dark:text-yellow-400',
    icon: 'text-yellow-500',
    Icon: AlertCircle,
  },
  danger: {
    container:
      'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/30 dark:border-red-800 dark:text-red-400',
    icon: 'text-red-500',
    Icon: XCircle,
  },
};

const Alert = React.forwardRef(
  (
    {
      children,
      variant = 'info',
      title,
      dismissible = false,
      onDismiss,
      onClose,
      icon: CustomIcon,
      animate = 'fade-up',
      animationDelay = 0,
      className = '',
      ...props
    },
    ref
  ) => {
    const config = variants[variant] || variants.info;
    const Icon = CustomIcon || config.Icon;
    const handleDismiss = onDismiss || onClose;

    return (
      <div
        ref={ref}
        className={cn(
          'flex items-start gap-3 rounded-lg border p-4',
          config.container,
          getAnimationClass(animate, animationDelay),
          className
        )}
        role="alert"
        {...props}
      >
        <Icon className={cn('h-5 w-5 shrink-0 mt-0.5', config.icon)} aria-hidden="true" />
        <div className="flex-1 min-w-0">
          {title && <p className="font-medium mb-1">{title}</p>}
          <div className="text-sm">{children}</div>
        </div>
        {dismissible && (
          <button
            type="button"
            onClick={handleDismiss}
            className="shrink-0 rounded-lg p-1 hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
            aria-label="Dismiss alert"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;
