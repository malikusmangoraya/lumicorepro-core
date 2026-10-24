import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  Bell,
  BriefcaseBusiness,
  ChevronRight,
  CreditCard,
  FileText,
  Gauge,
  LayoutDashboard,
  Menu,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Rocket,
  Settings,
  Sparkles,
  Sun,
  X,
} from 'lucide-react';
import BrandLogo from '../common/BrandLogo';
import SkipToContent from '../common/SkipToContent';
import { useTheme } from '../common/ThemeProvider';
import { cn } from '../../utils';

const NAV_ITEMS = [
  { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Generate', path: '/generate', icon: Sparkles },
  { label: 'Projects', path: '/gallery', icon: BriefcaseBusiness },
  { label: 'Agent Runs', path: '/workspace', icon: Activity },
  { label: 'Templates', path: '/templates', icon: FileText },
  { label: 'Analytics', path: '/ai-dashboard', icon: BarChart3 },
  { label: 'Integrations', path: '/api-settings', icon: Gauge },
  { label: 'Billing', path: '/billing', icon: CreditCard },
  { label: 'Settings', path: '/settings', icon: Settings },
];

const LOOP_PHASES = ['Brief', 'Strategy', 'Design', 'Build', 'Critique', 'Proof', 'Ship'];

function isActive(pathname, itemPath) {
  if (itemPath === '/dashboard') return pathname === '/dashboard';
  return pathname === itemPath || pathname.startsWith(`${itemPath}/`);
}

function ProductHeader({ onMenu, onToggleRail }) {
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/90 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMenu}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:hidden"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={onToggleRail}
            className="hidden h-10 w-10 items-center justify-center rounded-xl border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:inline-flex"
            aria-label="Toggle navigation rail"
          >
            <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
          </button>
          <div className="hidden items-center gap-2 text-sm text-muted-foreground sm:flex">
            <span className="font-medium text-foreground">Launch OS</span>
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Agent workspace</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))}
            className="hidden items-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:flex"
            aria-label="Open command palette"
          >
            <span>Command palette</span><kbd className="rounded bg-muted px-1.5 py-0.5 font-mono">Ctrl K</kbd>
          </button>
          <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground hover:bg-muted hover:text-foreground" aria-label="Notifications">
            <Bell className="h-4 w-4" aria-hidden="true" />
          </button>
          <button type="button" onClick={toggleTheme} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground hover:bg-muted hover:text-foreground" aria-label={isDark ? 'Use light theme' : 'Use dark theme'}>
            {isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
          </button>
          <button type="button" onClick={() => navigate('/profile')} className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground" aria-label="Open profile">LP</button>
        </div>
      </div>
    </header>
  );
}

function AgentRail({ collapsed, mobileOpen, onClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      {mobileOpen && <button type="button" className="fixed inset-0 z-40 bg-slate-950/50 lg:hidden" onClick={onClose} aria-label="Close navigation overlay" />}
      <aside className={cn('fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-background px-3 py-4 transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0', collapsed && 'lg:w-[78px]', mobileOpen ? 'translate-x-0' : '-translate-x-full')} aria-label="Agent OS navigation">
        <div className="flex items-center justify-between px-2 pb-6">
          <BrandLogo variant={collapsed ? 'mark' : 'lockup'} size={collapsed ? 'md' : 'sm'} />
          <button type="button" className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted lg:hidden" onClick={onClose} aria-label="Close navigation"><X className="h-4 w-4" aria-hidden="true" /></button>
        </div>
        <div className="mb-4 rounded-2xl border border-primary/20 bg-primary/[0.06] p-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-primary"><Rocket className="h-3.5 w-3.5" aria-hidden="true" />{!collapsed && 'Launch readiness'}</div>
          {!collapsed && <><div className="mt-2 text-sm font-semibold text-foreground">Build with proof</div><div className="mt-1 text-xs leading-relaxed text-muted-foreground">Every run moves from idea to evidence to ship.</div></>}
        </div>
        <nav className="space-y-1" aria-label="Primary">
          {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
            const active = isActive(location.pathname, path);
            return <button key={path} type="button" onClick={() => { navigate(path); onClose?.(); }} aria-current={active ? 'page' : undefined} className={cn('group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors', active ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' : 'text-muted-foreground hover:bg-muted hover:text-foreground', collapsed && 'lg:justify-center lg:px-2')}>
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span className={cn(collapsed && 'lg:hidden')}>{label}</span>
              {active && !collapsed && <ChevronRight className="ml-auto h-3.5 w-3.5" aria-hidden="true" />}
            </button>;
          })}
        </nav>
        <div className="mt-auto border-t border-border pt-4">
          <div className={cn('rounded-xl bg-muted/60 p-3', collapsed && 'lg:p-2')}>
            {!collapsed && <><div className="text-xs font-semibold text-foreground">Free workspace</div><div className="mt-1 text-xs text-muted-foreground">Upgrade when your launch volume grows.</div></>}
            {collapsed && <Sparkles className="mx-auto h-4 w-4 text-primary" aria-hidden="true" />}
          </div>
        </div>
      </aside>
    </>
  );
}

function LaunchLoop() {
  const pathname = useLocation().pathname;
  const current = pathname === '/generate' ? 0 : pathname === '/workspace' ? 5 : 1;
  return <div className="hidden border-b border-border/70 bg-muted/20 px-4 py-3 md:block sm:px-6"><div className="mx-auto flex max-w-[1600px] items-center gap-2 overflow-x-auto"><span className="mr-2 shrink-0 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">Launch loop</span>{LOOP_PHASES.map((phase, index) => <div key={phase} className="flex shrink-0 items-center gap-2"><span className={cn('flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold', index < current ? 'bg-emerald-500/15 text-emerald-700' : index === current ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}>{index + 1}</span><span className={cn('text-xs font-medium', index === current ? 'text-foreground' : 'text-muted-foreground')}>{phase}</span>{index < LOOP_PHASES.length - 1 && <span className="h-px w-4 bg-border" aria-hidden="true" />}</div>)}</div></div>;
}

export function AgentShellFrame({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  return <div className="min-h-screen bg-background text-foreground"><SkipToContent /><div className="flex min-h-screen"><AgentRail collapsed={collapsed} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} /><div className="min-w-0 flex-1"><ProductHeader onMenu={() => setMobileOpen(true)} onToggleRail={() => setCollapsed((value) => !value)} /><LaunchLoop /><main id="main-content" role="main" aria-label="Agent OS main content" className="min-h-[calc(100vh-64px)]"><div className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">{children}</div></main></div></div></div>;
}

export default function AgentShell() {
  return <AgentShellFrame><Outlet /></AgentShellFrame>;
}
