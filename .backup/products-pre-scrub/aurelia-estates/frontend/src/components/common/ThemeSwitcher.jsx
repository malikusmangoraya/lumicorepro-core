import React, { useEffect, useState } from 'react';
import { Moon, Sun, MonitorSmartphone } from 'lucide-react';
import { cn } from '../../utils';

const ThemeSwitcher = ({
  defaultTheme = 'system',
  storageKey = 'theme',
  options = ['light', 'dark', 'system'],
  className = '',
}) => {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(storageKey) || defaultTheme;
    } catch (e) {
      return defaultTheme;
    }
  });

  useEffect(() => {
    const root = document.documentElement;
    const resolved =
      theme === 'system'
        ? window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        : theme;
    root.classList.toggle('dark', resolved === 'dark');
    root.style.colorScheme = resolved;
    try {
      localStorage.setItem(storageKey, theme);
    } catch (e) {
      /* storage unavailable */
    }
  }, [theme, storageKey]);

  useEffect(() => {
    if (theme !== 'system') return undefined;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      document.documentElement.classList.toggle('dark', mq.matches);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  const icons = {
    light: Sun,
    dark: Moon,
    system: MonitorSmartphone,
  };

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded-full border bg-background p-1',
        className
      )}
      role="group"
      aria-label="Theme switcher"
    >
      {options.map((option) => {
        const Icon = icons[option];
        const active = theme === option;
        return (
          <button
            key={option}
            type="button"
            onClick={() => setTheme(option)}
            aria-pressed={active}
            aria-label={`${option} theme`}
            title={`${option} theme`}
            className={cn(
              'flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/40',
              active && 'bg-primary text-primary-foreground'
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
};

export default ThemeSwitcher;
