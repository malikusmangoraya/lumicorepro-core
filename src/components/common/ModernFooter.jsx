import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { ArrowUp, Zap } from 'lucide-react';
import { cn } from '@/utils';
import api from '@/services/api';
import BrandLogo from './BrandLogo';
import FooterNewsletter from './FooterNewsletter';
import { SocialIcons } from './socialIcons';
import { CurrencySelector } from './CurrencySelector';
import Language from './Language';

/**
 * Live status badge. Reads the real `/api/health` endpoint and reports exactly what
 * it finds — an unverified "99.99% operational" claim is not rendered, and an
 * unreachable backend is reported as unavailable rather than as healthy.
 */
function SystemStatusBadge() {
  const { t } = useTranslation();
  const { isPending, isError } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/health'),
    refetchInterval: 60000,
  });

  const healthy = !isPending && !isError;
  const label = isPending
    ? t('footer.statusChecking', 'Checking system status…')
    : healthy
      ? t('footer.statusOperational', 'API reachable — status OK')
      : t('footer.statusUnknown', 'Status unavailable');

  return (
    <div
      className={cn(
        'inline-flex w-fit items-center gap-2.5 rounded-full border px-3.5 py-1.5 text-xs font-medium',
        healthy
          ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
          : 'border-border bg-muted/40 text-muted-foreground'
      )}
    >
      <span className="relative flex h-2 w-2">
        {healthy && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
        )}
        <span
          className={cn(
            'relative inline-flex h-2 w-2 rounded-full',
            healthy ? 'bg-emerald-500' : 'bg-muted-foreground'
          )}
        />
      </span>
      <span>{label}</span>
    </div>
  );
}

export function ModernFooter({
  brandName = 'LumicorePro',
  tagline = 'Next-generation AI-powered fullstack application platform. Built with React 19, Vite, and high-performance micro-interactions.',
  columns,
  showNewsletter = true,
  showStatus = true,
  className = '',
}) {
  const { t } = useTranslation();

  // Every href below resolves to a route that exists in `src/routes/index.jsx`.
  const defaultColumns = [
    {
      title: t('footer.platform', 'Platform'),
      links: [
        { label: t('footer.aiGenerator', 'AI Generator'), href: '/generate', badge: 'Hot' },
        { label: t('footer.templateGallery', 'Template Gallery'), href: '/templates', badge: 'New' },
        {
          label: t('footer.ecommerceEngine', 'E-Commerce Engine'),
          href: '/templates/ecommerce/ProductListing',
        },
        {
          label: t('footer.analyticsDashboard', 'Analytics Dashboard'),
          href: '/templates/dashboard/DashboardOverview',
        },
        { label: t('footer.pricing', 'Pricing Plans'), href: '/pricing' },
      ],
    },
    {
      title: t('footer.solutions', 'Solutions'),
      links: [
        {
          label: t('footer.enterprise', 'Enterprise SaaS'),
          href: '/templates/business/LandingPage',
        },
        { label: t('footer.fintech', 'Fintech & Banking'), href: '/templates/business/PricingPage' },
        {
          label: t('footer.healthcare', 'Healthcare Portal'),
          href: '/templates/healthcare/MedicalPortal',
        },
        {
          label: t('footer.restaurant', 'Restaurant & Hospitality'),
          href: '/templates/restaurant/RestaurantMenu',
        },
        {
          label: t('footer.realEstate', 'Real Estate Platform'),
          href: '/templates/realestate/PropertyListing',
        },
      ],
    },
    {
      title: t('footer.resources', 'Resources'),
      links: [
        { label: t('footer.caseStudies', 'Case Studies'), href: '/gallery' },
        { label: t('footer.productOverview', 'Product Overview'), href: '/marketing' },
        { label: t('footer.boilerplate', 'Marketplace Kit'), href: '/boilerplate' },
        { label: t('footer.apiSettings', 'API Settings'), href: '/api-settings' },
        { label: t('footer.register', 'Create Account'), href: '/register' },
      ],
    },
    {
      title: t('footer.legal', 'Legal & Trust'),
      links: [
        { label: t('footer.privacy', 'Privacy Policy'), href: '/privacy' },
        { label: t('footer.terms', 'Terms of Service'), href: '/terms' },
        { label: t('footer.refund', 'Refund Policy'), href: '/refund' },
        {
          label: t('footer.cookiePreferences', 'Cookie Preferences'),
          action: 'cookiePreferences',
        },
      ],
    },
  ];

  const activeColumns = columns || defaultColumns;

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const openCookiePreferences = () => {
    window.dispatchEvent(new Event('cookiePreferences'));
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
              <BrandLogo variant="lockup" name={brandName} size="lg" />
              <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
                {tagline}
              </p>
            </div>

            {showStatus && <SystemStatusBadge />}

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
          <section aria-labelledby="footer-sections-heading" className="lg:col-span-4">
            <h2 id="footer-sections-heading" className="sr-only">
              Footer navigation
            </h2>
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
              {activeColumns.map((col) => (
                <div key={col.title} className="space-y-4">
                  <h3 className="font-display text-sm font-semibold tracking-wider text-foreground uppercase">
                    {col.title}
                  </h3>
                  <ul className="space-y-2.5" role="list">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      {link.action === 'cookiePreferences' ? (
                        <button
                          type="button"
                          onClick={openCookiePreferences}
                          className="text-sm text-muted-foreground transition-colors hover:text-primary"
                        >
                          {link.label}
                        </button>
                      ) : (
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
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Newsletter Banner */}
        {showNewsletter && (
          <div className="mt-14 rounded-2xl border border-border/70 bg-muted/30 p-6 md:p-8 backdrop-blur-sm">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="space-y-1">
                <h3 className="font-display text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                  <Zap className="h-5 w-5 text-primary" aria-hidden="true" />
                  {t('footer.newsletterTitle', 'Stay ahead of modern web design')}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {t(
                    'footer.newsletterSubtitle',
                    'Subscribe to receive weekly components, UI templates, and AI generation insights.'
                  )}
                </p>
              </div>

              <FooterNewsletter />
            </div>
          </div>
        )}

        {/* Bottom Bar */}
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border/60 pt-8 text-xs text-muted-foreground">
          <div className="flex flex-wrap items-center gap-4">
            <p>
              &copy; {new Date().getFullYear()} {brandName}. All rights reserved.
            </p>
            <span className="hidden sm:inline">&bull;</span>
            <div className="flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
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
