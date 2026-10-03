import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Menu, X, Home, BarChart3, Settings, Bell, ChevronRight } from 'lucide-react';
import { BrandLogo } from '../components/common';
import NotificationBell from '../components/common/NotificationBell';
import SkipToContent from '../components/common/SkipToContent';
import { useTheme } from '../components/common/ThemeProvider';
import { cn } from '../utils';

const sidebarItems = [
  { path: '/dashboard', label: 'Overview', icon: Home },
  { path: '/dashboard/usage', label: 'Usage', icon: BarChart3 },
  { path: '/notifications', label: 'Notifications', icon: Bell },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <SkipToContent />

      <div className="flex flex-1">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden animate-fade-in"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <aside
          role="complementary"
          aria-label="Dashboard sidebar"
          className={cn(
            'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card',
            'transition-transform duration-300 ease-in-out',
            'lg:translate-x-0 lg:static lg:z-auto',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex h-16 items-center justify-between border-b border-border px-4">
            <Link to="/" className="inline-flex items-center" aria-label="LumicorePro home">
              <BrandLogo variant="full" size="sm" />
            </Link>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          <nav aria-label="Dashboard navigation" className="flex-1 overflow-y-auto p-3 space-y-1">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                    active
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/70'
                  )}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon className="h-4 w-4 shrink-0" strokeWidth={2} aria-hidden="true" />
                  <span>{item.label}</span>
                  {active && (
                    <ChevronRight className="ml-auto h-4 w-4 text-primary/50" aria-hidden="true" />
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-border p-3">
            <button
              type="button"
              onClick={toggleTheme}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/70 transition-colors"
              aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              <span className="h-4 w-4 flex items-center justify-center" aria-hidden="true">
                {isDark ? '☀️' : '🌙'}
              </span>
              <span>{isDark ? 'Light mode' : 'Dark mode'}</span>
            </button>
          </div>
        </aside>

        {/* Main content */}
        <div className="flex flex-1 flex-col min-w-0">
          {/* Top bar */}
          <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/90 backdrop-blur-md supports-[backdrop-filter]:bg-background/75 px-4 lg:px-6">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu className="h-5 w-5" aria-hidden="true" />
            </button>

            <div className="flex-1" />

            <span className="hidden md:inline-flex">
              <NotificationBell />
            </span>
          </header>

          <main id="main-content" role="main" aria-label="Dashboard content" className="flex-1">
            <div className="container mx-auto px-4 py-6 lg:px-6 lg:py-8 animate-page-enter">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
