import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Sparkles,
  ArrowUp,
  Mail,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { cn } from '@/utils';
import UniqueLogo from './UniqueLogo';
import { Button } from '../ui';
import { CurrencySelector } from '../CurrencySelector';
import Language from './Language';

// Self-contained, resilient Social SVG Icons
const SocialIcons = {
  Twitter: (props) => (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" {...props}>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  ),
  Github: (props) => (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" {...props}>
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  ),
  Linkedin: (props) => (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" {...props}>
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.62 1.62 0 1 0 0 3.24 1.62 1.62 0 0 0 0-3.24z" />
    </svg>
  ),
  Discord: (props) => (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" {...props}>
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.893.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  ),
};

export function ModernFooter({
  brandName = 'LumicorePro',
  tagline = 'Next-generation AI-powered fullstack application platform. Built with React 19, Vite, and high-performance micro-interactions.',
  columns,
  showNewsletter = true,
  showStatus = true,
  className = '',
}) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  const defaultColumns = [
    {
      title: 'Platform',
      links: [
        { label: 'AI Generator', href: '/generate', badge: 'Hot' },
        { label: 'UI Motion Kit', href: '/templates', badge: 'New' },
        { label: 'Template Gallery', href: '/templates' },
        { label: 'E-Commerce Engine', href: '/templates/ecommerce/ProductListing' },
        { label: 'Analytics Dashboard', href: '/templates/dashboard/DashboardOverview' },
      ],
    },
    {
      title: 'Solutions',
      links: [
        { label: 'Enterprise SaaS', href: '/templates/business/LandingPage' },
        { label: 'Fintech & Banking', href: '/pricing' },
        { label: 'Healthcare Portal', href: '/templates/healthcare/MedicalPortal' },
        { label: 'Restaurant & Hospitality', href: '/templates/restaurant/RestaurantMenu' },
        { label: 'Real Estate Platform', href: '/templates/realestate/PropertyListing' },
      ],
    },
    {
      title: 'Resources',
      links: [
        { label: 'Documentation', href: '/docs' },
        { label: 'API Reference', href: '/api-settings' },
        { label: 'Component Library', href: '/templates' },
        { label: 'Pricing Plans', href: '/pricing' },
        { label: 'Release Notes', href: '/templates' },
      ],
    },
    {
      title: 'Legal & Trust',
      links: [
        { label: 'Privacy Policy', href: '/privacy-policy' },
        { label: 'Terms of Service', href: '/terms-of-service' },
        { label: 'Refund Policy', href: '/refund-policy' },
        { label: 'Security & Compliance', href: '/pricing' },
        { label: 'Cookie Preferences', href: '#' },
      ],
    },
  ];

  const activeColumns = columns || defaultColumns;

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) return;
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSubscribed(true);
    }, 600);
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer
      role="contentinfo"
      aria-label="Site Footer"
      className={cn(
        'relative border-t border-border/80 bg-card text-foreground transition-colors overflow-hidden',
        className
      )}
    >
      {/* Top subtle glow bar */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[1px] w-3/4 bg-gradient-to-r from-transparent via-primary/50 to-transparent" />

      <div className="container mx-auto px-4 py-16 lg:py-20">
        {/* Main Grid */}
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-6 lg:gap-8">
          {/* Brand Info (2 Columns) */}
          <div className="lg:col-span-2 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <UniqueLogo name={brandName} size="lg" />
              <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
                {tagline}
              </p>
            </div>

            {/* Live System Status */}
            {showStatus && (
              <div className="inline-flex items-center gap-2.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400 w-fit">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                <span>All systems operational &bull; 99.99%</span>
              </div>
            )}

            {/* Social Icons */}
            <div className="flex items-center gap-3 text-muted-foreground">
              {[
                { icon: SocialIcons.Twitter, href: 'https://twitter.com', label: 'Twitter' },
                { icon: SocialIcons.Github, href: 'https://github.com', label: 'GitHub' },
                { icon: SocialIcons.Linkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
                { icon: SocialIcons.Discord, href: 'https://discord.com', label: 'Discord' },
              ].map((s) => (
                <a
                  key={s.label}
                  href={s.href}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={s.label}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-border/80 bg-background/50 transition-all duration-200 hover:border-primary hover:bg-primary/10 hover:text-primary active:scale-95"
                >
                  <s.icon />
                </a>
              ))}
            </div>
          </div>

          {/* Links Columns (4 Columns on Desktop) */}
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4 lg:col-span-4">
            {activeColumns.map((col) => (
              <div key={col.title} className="space-y-4">
                <h4 className="font-display text-sm font-semibold tracking-wider text-foreground uppercase">
                  {col.title}
                </h4>
                <ul className="space-y-2.5" role="list">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      <Link
                        to={link.href}
                        className="group inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-primary"
                      >
                        <span>{link.label}</span>
                        {link.badge && (
                          <span className="rounded-full bg-primary/10 px-1.5 py-0.2 text-[10px] font-semibold text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                            {link.badge}
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Newsletter Banner */}
        {showNewsletter && (
          <div className="mt-14 rounded-2xl border border-border/70 bg-muted/30 p-6 md:p-8 backdrop-blur-sm">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="space-y-1">
                <h3 className="font-display text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" /> Stay ahead of modern web design
                </h3>
                <p className="text-sm text-muted-foreground">
                  Subscribe to receive weekly components, UI templates, and AI generation insights.
                </p>
              </div>

              {subscribed ? (
                <div className="flex items-center gap-2 text-emerald-500 font-medium text-sm">
                  <CheckCircle2 className="h-5 w-5" /> You are subscribed! Welcome aboard.
                </div>
              ) : (
                <form onSubmit={handleSubscribe} className="flex w-full md:w-auto items-center gap-2">
                  <div className="relative flex-1 md:w-72">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your work email"
                      className="w-full rounded-xl border border-border/80 bg-background/90 pl-9 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                  <Button type="submit" variant="primary" disabled={loading} className="shrink-0">
                    {loading ? 'Joining...' : 'Subscribe'}
                  </Button>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Bottom Bar */}
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border/60 pt-8 text-xs text-muted-foreground">
          <div className="flex flex-wrap items-center gap-4">
            <p>&copy; {new Date().getFullYear()} {brandName}. All rights reserved.</p>
            <span className="hidden sm:inline">&bull;</span>
            <div className="flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-primary" />
              <span>React 19 &bull; Vite &bull; Tailwind CSS &bull; Motion</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3">
              <Language />
              <CurrencySelector />
            </div>

            <button
              onClick={scrollToTop}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border/80 bg-background hover:bg-accent text-foreground transition-all active:scale-95"
              aria-label="Back to top"
              title="Back to top"
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default ModernFooter;
