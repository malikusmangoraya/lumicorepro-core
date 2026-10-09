/**
 * brand-shells.cjs — the alternative layout shells and the Hero primitive stop being the
 * template's generic boilerplate.
 *
 * Before: LandingLayout hard-coded the wordmark "PlatformPro" on slate-950/cyan-400,
 * AppLayout hard-coded "ConsoleAdmin" on the same palette, and business/Hero was identical in
 * ten products with English-only copy. None of the three imported BRAND, the design tokens or
 * i18n, so a real-estate listing site and a photography studio shipped the same dark SaaS
 * shell.
 *
 * After: each file reads the product's own BRAND.js, its --t-* tokens and i18n, and each
 * product gets one of three genuinely different header/footer arrangements. The Hero carries
 * a per-product composition (split, editorial, cinematic, utility) chosen to suit the niche.
 *
 * Run: node products/_audit/brand-shells.cjs
 */
const fs = require('fs');

/** nav arrangement + hero composition per product, matched to the niche. */
const DNA = {
  apex: { nav: 'utility-rail', hero: 'split-metric', eyebrow: 'Conversion engineering', cta: 'Start free' },
  'aurelia-estates': { nav: 'centered-hairline', hero: 'cinematic-search', eyebrow: 'Private brokerage', cta: 'Book a viewing' },
  'aurum-fitness': { nav: 'bold-band', hero: 'stat-band', eyebrow: 'Coaching floors', cta: 'Claim trial' },
  'claimflow-ai': { nav: 'utility-rail', hero: 'product-frame', eyebrow: 'Claims operations', cta: 'Open console' },
  flowpilot: { nav: 'segmented', hero: 'bento-nodes', eyebrow: 'Workflow automation', cta: 'Map a flow' },
  'meridian-capital': { nav: 'centered-hairline', hero: 'numbers-first', eyebrow: 'Private capital', cta: 'Request deck' },
  'nuage-events': { nav: 'overlay-ticker', hero: 'cinematic-search', eyebrow: 'Event production', cta: 'Check availability' },
  'prestige-studio': { nav: 'indexed', hero: 'editorial', eyebrow: 'Design studio', cta: 'View work' },
  resupro: { nav: 'segmented', hero: 'product-frame', eyebrow: 'Career tooling', cta: 'Build a resume' },
  'saffron-voyage': { nav: 'overlay-ticker', hero: 'collage', eyebrow: 'Private itineraries', cta: 'Plan a journey' },
  'studio-lumen': { nav: 'indexed', hero: 'editorial', eyebrow: 'Photography', cta: 'Enquire' },
};

const NAV_LINKS = [
  { path: '/', key: 'home', label: 'Home' },
  { path: '/about', key: 'about', label: 'About' },
  { path: '/services', key: 'services', label: 'Services' },
  { path: '/pricing', key: 'pricing', label: 'Pricing' },
  { path: '/contact', key: 'contact', label: 'Contact' },
];

const header = (nav, brandName, dna) => {
  const links = NAV_LINKS.map(
    (l) => `          <li>
            <Link to="${l.path}" className="hover:opacity-80 transition-opacity">
              {t('common.${l.key}', '${l.label}')}
            </Link>
          </li>`
  ).join('\n');

  const inner = {
    'utility-rail': `      <div className="border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-2 text-xs" style={{ color: 'var(--t-muted)' }}>
          <span>{t('common.status', 'All systems operational')}</span>
          <span>{BRAND.name}</span>
        </div>
      </div>
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <BrandLockup size={32} />
        <nav aria-label="Primary">
          <ul className="hidden items-center gap-7 text-sm font-medium md:flex">
${links}
          </ul>
        </nav>
        <Link to="/register" className="btn-primary">{t('common.get_started', '${dna.cta}')}</Link>
      </div>`,
    'centered-hairline': `      <div className="mx-auto max-w-5xl px-6 py-6 text-center">
        <BrandLockup size={30} className="justify-center" />
        <p className="mt-2 text-xs uppercase tracking-[0.28em]" style={{ color: 'var(--t-muted)' }}>
          {t('common.tagline', '${dna.eyebrow}')}
        </p>
        <nav aria-label="Primary" className="mt-4 border-y py-3" style={{ borderColor: 'var(--t-border)' }}>
          <ul className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-xs uppercase tracking-[0.18em]">
${links}
          </ul>
        </nav>
      </div>`,
    'bold-band': `      <div className="px-6 py-5" style={{ backgroundColor: 'var(--t-primary)' }}>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4">
          <BrandLockup size={30} dark />
          <nav aria-label="Primary">
            <ul className="flex flex-wrap items-center gap-6 text-sm font-black uppercase tracking-widest text-white">
${links}
            </ul>
          </nav>
        </div>
      </div>`,
    segmented: `      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-4">
        <BrandLockup size={30} />
        <nav aria-label="Primary" className="rounded-full border p-1" style={{ borderColor: 'var(--t-border)' }}>
          <ul className="flex items-center gap-1 text-sm">
${links}
          </ul>
        </nav>
        <Link to="/contact" className="btn-outline">{t('common.talk_to_us', '${dna.cta}')}</Link>
      </div>`,
    'overlay-ticker': `      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <BrandLockup size={32} dark />
        <nav aria-label="Primary">
          <ul className="hidden items-center gap-7 text-sm text-white md:flex">
${links}
          </ul>
        </nav>
      </div>
      <div className="overflow-hidden border-t border-white/15 py-2 text-xs uppercase tracking-[0.3em] text-white/80">
        <span className="mx-auto block max-w-7xl px-6">
          {BRAND.name} — {t('common.tagline', '${dna.eyebrow}')}
        </span>
      </div>`,
    indexed: `      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span className="text-xs tabular-nums" style={{ color: 'var(--t-muted)' }}>01 / {BRAND.initials}</span>
        <BrandLockup size={28} />
        <nav aria-label="Primary">
          <ul className="hidden items-center gap-6 text-xs uppercase tracking-[0.2em] md:flex">
${links}
          </ul>
        </nav>
      </div>`,
  };

  return `    <header className="sticky top-0 z-40 backdrop-blur" style={{ backgroundColor: 'color-mix(in srgb, var(--t-canvas) 88%, transparent)', color: nav === 'bold-band' || nav === 'overlay-ticker' ? '#fff' : 'var(--t-text)' }}>
${inner[nav]}
    </header>`;
};

const footer = (dna) => `    <footer style={{ backgroundColor: 'var(--t-footer)' }} className="mt-auto text-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-3">
          <BrandLockup size={30} dark />
          <p className="max-w-xs text-sm leading-relaxed text-white/70">
            {t('footer.blurb', '${dna.eyebrow} — built for people who care about the details.')}
          </p>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">{t('footer.product', 'Product')}</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/services" className="hover:text-white">{t('common.services', 'Services')}</Link></li>
            <li><Link to="/pricing" className="hover:text-white">{t('common.pricing', 'Pricing')}</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">{t('footer.company', 'Company')}</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/about" className="hover:text-white">{t('common.about', 'About')}</Link></li>
            <li><Link to="/contact" className="hover:text-white">{t('common.contact', 'Contact')}</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">{t('footer.legal', 'Legal')}</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/privacy" className="hover:text-white">{t('common.privacy', 'Privacy')}</Link></li>
            <li><Link to="/terms" className="hover:text-white">{t('common.terms', 'Terms')}</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-4 text-xs text-white/60">
          <span>© {new Date().getFullYear()} {BRAND.name} — {t('common.tagline', '${dna.eyebrow}')}</span>
          <span>{t('footer.built_with', 'React 19 · Vite · Tailwind')}</span>
        </div>
      </div>
    </footer>`;

const LANDING = (dna, brand) => `/**
 * LandingLayout — brand shell for marketing routes.
 *
 * Reads this product's BRAND.js, its --t-* tokens and i18n. It is registered through
 * lib/LazyLayouts.jsx as an alternative to a page composing Navbar/Footer itself.
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import BrandLockup from '../components/brand/BrandLockup';
import { BRAND } from '../components/brand/BRAND';

export default function LandingLayout({ children }) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col" style={{ backgroundColor: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <a href="#main-content" className="skip-link">
        {t('common.skip_to_content', 'Skip to content')}
      </a>
${header(dna.nav, brand, dna)}
      <main id="main-content" className="flex-1">
        {children}
      </main>
${footer(dna)}
    </div>
  );
}
`;

const APP = (dna) => `/**
 * AppLayout — brand shell for signed-in / console routes.
 *
 * Layout arrangement: ${dna.nav}. Colours come from the same --t-* tokens as the marketing
 * shell, so the console cannot drift away from the brand.
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BarChart3, Bell, Menu, Settings, Users } from 'lucide-react';
import BrandLockup from '../components/brand/BrandLockup';
import { BRAND } from '../components/brand/BRAND';

export default function AppLayout({ children }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const items = [
    { to: '/admin', label: t('common.overview', 'Overview'), icon: BarChart3 },
    { to: '/account', label: t('common.account', 'Account'), icon: Users },
    { to: '/admin', label: t('common.settings', 'Settings'), icon: Settings },
  ];

  return (
    <div className="flex min-h-screen flex-col" style={{ backgroundColor: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <header className="border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-center gap-3">
            <BrandLockup size={28} />
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
              style={{ backgroundColor: 'var(--t-primary)', color: '#fff' }}
            >
              {t('common.console', '${dna.eyebrow} console')}
            </span>
          </div>
          <button
            type="button"
            className="md:hidden"
            aria-expanded={open}
            aria-label={t('common.toggle_nav', 'Toggle navigation')}
            onClick={() => setOpen((value) => !value)}
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <nav aria-label="Console" className="hidden items-center gap-1 md:flex">
            {items.map(({ to, label, icon: Icon }) => (
              <Link key={label} to={to} className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:opacity-80">
                <Icon className="h-4 w-4" aria-hidden="true" />
                {label}
              </Link>
            ))}
            <span className="ml-3 flex items-center gap-2 border-l pl-4 text-sm" style={{ borderColor: 'var(--t-border)' }}>
              <Bell className="h-4 w-4" aria-hidden="true" />
              {BRAND.initials}
            </span>
          </nav>
        </div>
        {open && (
          <nav aria-label="Console" className="border-t px-6 py-3 md:hidden" style={{ borderColor: 'var(--t-border)' }}>
            <ul className="space-y-2 text-sm">
              {items.map(({ to, label }) => (
                <li key={label}>
                  <Link to={to}>{label}</Link>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </header>
      <main id="main-content" className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        {children}
      </main>
    </div>
  );
}
`;

/** Hero composition per product, so the primitive is not one template repeated eleven times. */
const HERO_BODY = {
  'split-metric': `        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            {renderBadge()}
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.08] sm:text-5xl">{title} <span style={{ color: 'var(--t-primary)' }}>{highlight}</span></h1>
            <p className="mt-5 max-w-xl text-base sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
            {renderActions()}
          </div>
          <div className="card-panel p-6">
            <dl className="grid grid-cols-2 gap-6">
              {metrics.map((metric) => (
                <div key={metric.label}>
                  <dt className="text-xs uppercase tracking-wider" style={{ color: 'var(--t-muted)' }}>{metric.label}</dt>
                  <dd className="mt-1 text-3xl font-bold lumi-count" style={{ color: 'var(--t-primary)' }}>{metric.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>`,
  'cinematic-search': `        <div className="relative overflow-hidden rounded-2xl" style={{ backgroundColor: 'var(--t-heading)' }}>
          <LazyImage src={image} alt={imageAlt} className="h-[24rem] w-full object-cover opacity-80 sm:h-[32rem]" />
          <div className="absolute inset-0 flex flex-col justify-end gap-4 p-8 text-white sm:p-12">
            {renderBadge()}
            <h1 className="max-w-3xl text-4xl font-extrabold leading-[1.08] sm:text-5xl">{title} <span style={{ color: 'var(--t-accent)' }}>{highlight}</span></h1>
            <p className="max-w-2xl text-base text-white/80 sm:text-lg">{subtitle}</p>
            {renderActions()}
          </div>
        </div>`,
  'stat-band': `        <div>
          {renderBadge()}
          <h1 className="mt-5 max-w-4xl text-4xl font-black uppercase leading-[1.05] sm:text-6xl">{title} <span style={{ color: 'var(--t-primary)' }}>{highlight}</span></h1>
          <p className="mt-5 max-w-2xl text-base sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
          {renderActions()}
          <dl className="mt-12 grid grid-cols-2 gap-px overflow-hidden rounded-xl border sm:grid-cols-4" style={{ borderColor: 'var(--t-border)', backgroundColor: 'var(--t-border)' }}>
            {metrics.map((metric) => (
              <div key={metric.label} className="p-5" style={{ backgroundColor: 'var(--t-surface)' }}>
                <dt className="text-xs uppercase tracking-wider" style={{ color: 'var(--t-muted)' }}>{metric.label}</dt>
                <dd className="mt-1 text-2xl font-bold lumi-count">{metric.value}</dd>
              </div>
            ))}
          </dl>
        </div>`,
  'product-frame': `        <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
          <div>
            {renderBadge()}
            <h1 className="mt-5 text-3xl font-extrabold leading-tight sm:text-4xl">{title} <span style={{ color: 'var(--t-primary)' }}>{highlight}</span></h1>
            <p className="mt-4 text-base" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
            {renderActions()}
          </div>
          <div className="overflow-hidden rounded-xl border" style={{ borderColor: 'var(--t-border)', backgroundColor: 'var(--t-surface)' }}>
            <div className="flex items-center gap-1.5 border-b px-3 py-2" style={{ borderColor: 'var(--t-border)' }}>
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: 'var(--t-accent)' }} />
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: 'var(--t-muted)' }} />
              <span className="ml-2 text-xs" style={{ color: 'var(--t-muted)' }}>{BRAND.name}</span>
            </div>
            <LazyImage src={image} alt={imageAlt} className="h-64 w-full object-cover sm:h-80" />
          </div>
        </div>`,
  'bento-nodes': `        <div>
          {renderBadge()}
          <h1 className="mt-5 max-w-3xl text-4xl font-extrabold leading-[1.08] sm:text-5xl">{title} <span style={{ color: 'var(--t-primary)' }}>{highlight}</span></h1>
          <p className="mt-5 max-w-2xl text-base sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
          {renderActions()}
          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            <div className="card-panel sm:col-span-2 p-6">
              <p className="text-xs uppercase tracking-wider" style={{ color: 'var(--t-muted)' }}>{t('hero.flow', 'Flow')}</p>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {metrics.map((metric) => (
                  <span key={metric.label} className="rounded-full border px-3 py-1 text-xs" style={{ borderColor: 'var(--t-border)' }}>
                    {metric.label} · <strong>{metric.value}</strong>
                  </span>
                ))}
              </div>
            </div>
            <div className="card-panel p-6">
              <LazyImage src={image} alt={imageAlt} className="h-32 w-full rounded object-cover" />
            </div>
          </div>
        </div>`,
  'numbers-first': `        <div className="max-w-3xl">
          {renderBadge()}
          <h1 className="mt-5 text-4xl font-normal leading-[1.15] sm:text-5xl">{title} <span style={{ color: 'var(--t-primary)' }}>{highlight}</span></h1>
          <p className="mt-6 text-base leading-relaxed sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
          {renderActions()}
          <dl className="mt-14 divide-y" style={{ borderColor: 'var(--t-border)' }}>
            {metrics.map((metric) => (
              <div key={metric.label} className="flex items-baseline justify-between gap-6 border-t py-4" style={{ borderColor: 'var(--t-border)' }}>
                <dt className="text-sm" style={{ color: 'var(--t-muted)' }}>{metric.label}</dt>
                <dd className="text-2xl font-semibold tabular-nums">{metric.value}</dd>
              </div>
            ))}
          </dl>
        </div>`,
  editorial: `        <div>
          <div className="flex flex-wrap items-baseline justify-between gap-4">
            {renderBadge()}
            <span className="text-xs uppercase tracking-[0.3em]" style={{ color: 'var(--t-muted)' }}>{BRAND.initials}</span>
          </div>
          <h1 className="mt-6 max-w-4xl text-5xl font-bold leading-[1.02] sm:text-7xl">{title} <em className="not-italic" style={{ color: 'var(--t-primary)' }}>{highlight}</em></h1>
          <p className="mt-7 max-w-2xl text-base leading-relaxed sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
          {renderActions()}
          <div className="mt-14 grid gap-3 sm:grid-cols-3">
            <LazyImage src={image} alt={imageAlt} className="h-56 w-full rounded object-cover sm:col-span-2" />
            <div className="card-panel p-6">
              <ul className="space-y-3 text-sm">
                {metrics.map((metric) => (
                  <li key={metric.label} className="flex justify-between gap-3">
                    <span style={{ color: 'var(--t-muted)' }}>{metric.label}</span>
                    <strong>{metric.value}</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>`,
  collage: `        <div className="grid gap-8 lg:grid-cols-[1.1fr_1fr] lg:items-center">
          <div>
            {renderBadge()}
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] sm:text-5xl">{title} <span style={{ color: 'var(--t-accent)' }}>{highlight}</span></h1>
            <p className="mt-5 text-base sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
            {renderActions()}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <LazyImage src={image} alt={imageAlt} className="col-span-2 h-56 w-full rounded-xl object-cover" />
            {metrics.slice(0, 2).map((metric) => (
              <div key={metric.label} className="card-panel p-4">
                <p className="text-xs uppercase tracking-wider" style={{ color: 'var(--t-muted)' }}>{metric.label}</p>
                <p className="mt-1 text-xl font-bold">{metric.value}</p>
              </div>
            ))}
          </div>
        </div>`,
};

const HERO = (dna, art) => `/**
 * Hero — the page-opening composition for this product.
 *
 * Variant: ${dna.hero}. Copy comes from the caller or from i18n, and every colour is a
 * --t-* token, so the same primitive renders differently for each brand rather than being one
 * hard-coded dark template shared by every product.
 *
 * The artwork is a real asset that ships with this product and is imported so the bundler
 * fingerprints it. (The previous version imported \`img\` from utils.js, which never exported
 * it — a latent build failure for anything that wired this component up.)
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight, PlayCircle, Sparkles } from 'lucide-react';
import LazyImage from '../common/LazyImage';
import defaultImage from '../../assets/images/${art.file}';
import { cn } from '../../utils';
import { BRAND } from '../brand/BRAND';

const Hero = ({
  badge,
  title,
  highlight,
  subtitle,
  primaryLabel,
  secondaryLabel,
  onPrimary,
  onSecondary,
  image = defaultImage,
  imageAlt = '${art.alt}',
  metrics = [],
  className = '',
}) => {
  const { t } = useTranslation();
  const resolvedTitle = title || t('hero.title', 'Work that speaks for itself');
  const resolvedHighlight = highlight || t('hero.highlight', BRAND.name);
  const resolvedSubtitle =
    subtitle || t('hero.subtitle', 'A complete platform for teams who care about craft, speed and detail.');
  const resolvedMetrics = metrics.length
    ? metrics
    : [
        { label: t('hero.metric_1', 'Projects delivered'), value: '1,200+' },
        { label: t('hero.metric_2', 'Client retention'), value: '98%' },
        { label: t('hero.metric_3', 'Avg. response'), value: '< 4h' },
      ];

  const renderBadge = () =>
    badge === null ? null : (
      <span
        className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium"
        style={{ borderColor: 'var(--t-border)', color: 'var(--t-primary)' }}
      >
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        {badge || t('hero.badge', '${dna.eyebrow}')}
      </span>
    );

  const renderActions = () => (
    <div className="mt-8 flex flex-col gap-3 sm:flex-row">
      <button type="button" onClick={onPrimary} className="btn-primary justify-center">
        {primaryLabel || t('hero.primary', '${dna.cta}')}
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </button>
      <button type="button" onClick={onSecondary} className="btn-outline justify-center">
        <PlayCircle className="h-4 w-4" aria-hidden="true" />
        {secondaryLabel || t('hero.secondary', 'See it in action')}
      </button>
    </div>
  );

  return (
    <section className={cn('relative overflow-hidden px-6 py-16 sm:py-24', className)}>
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        style={{ background: 'radial-gradient(60% 50% at 50% 0%, color-mix(in srgb, var(--t-primary) 12%, transparent), transparent 70%)' }}
      />
      <div className="relative mx-auto max-w-7xl">
${HERO_BODY[dna.hero]}
      </div>
    </section>
  );
};

export default Hero;
`;

// One real, shipped asset per product, chosen from what that product actually has on disk.
const ART = {
  apex: { file: 'strategy.jpg', alt: 'Team reviewing growth plans' },
  'aurelia-estates': { file: 'building-modern.jpg', alt: 'A modern residence' },
  'aurum-fitness': { file: 'professional-male.jpg', alt: 'A coach on the training floor' },
  'claimflow-ai': { file: 'hero-desk.jpg', alt: 'An adjuster working a claim' },
  flowpilot: { file: 'work-meeting2.jpg', alt: 'A team mapping a workflow' },
  'meridian-capital': { file: 'city.jpg', alt: 'A financial district at dusk' },
  'nuage-events': { file: 'office-team.jpg', alt: 'Producers planning an event' },
  'prestige-studio': { file: 'corporate-space.jpg', alt: 'A studio space' },
  resupro: { file: 'corporate-hero.jpg', alt: 'A professional at work' },
  'saffron-voyage': { file: 'hero.jpg', alt: 'A destination at golden hour' },
  'studio-lumen': { file: 'focus-work.jpg', alt: 'A photographer at work' },
};

const report = [];
for (const [id, dna] of Object.entries(DNA)) {
  const src = `products/${id}/frontend/src`;
  const brandSrc = fs.readFileSync(`${src}/components/brand/BRAND.js`, 'utf8');
  const brand = (brandSrc.match(/name:\s*"([^"]*)"/) || [])[1] || id;
  const art = ART[id];
  if (!fs.existsSync(`${src}/assets/images/${art.file}`)) {
    throw new Error(`${id}: default hero artwork not found: ${art.file}`);
  }

  const files = {
    [`${src}/layouts/LandingLayout.jsx`]: LANDING(dna, brand),
    [`${src}/layouts/AppLayout.jsx`]: APP(dna),
    [`${src}/components/business/Hero.jsx`]: HERO(dna, art),
  };
  for (const [path, content] of Object.entries(files)) {
    fs.writeFileSync(path, content.replace(/\n/g, '\r\n'));
  }
  // The generic boilerplate must be gone from every shipped shell.
  const text = Object.keys(files)
    .map((f) => fs.readFileSync(f, 'utf8'))
    .join('\n');
  report.push({
    id,
    nav: dna.nav,
    hero: dna.hero,
    platformProGone: !/PlatformPro|ConsoleAdmin/.test(text),
    brandAware: /from '\.\..*brand\/BRAND'|from '\.\/brand\/BRAND'|from '\.\.\/brand\/BRAND'/.test(text),
    i18nAware: /useTranslation/.test(text),
    realAsset: /from '\.\.\/\.\.\/assets\/images\//.test(text),
    hardcodedSlate: (text.match(/slate-(9|8)\d\d/g) || []).length,
  });
}

console.log('product            | nav arrangement     | hero variant     | PlatformPro gone | brand | i18n | slate-950 left');
console.log('-------------------|---------------------|------------------|------------------|-------|------|---------------');
for (const r of report) {
  console.log(
    `${r.id.padEnd(18)} | ${r.nav.padEnd(19)} | ${r.hero.padEnd(16)} | ${r.platformProGone ? '       ok        ' : '       NO        '} | ${r.brandAware ? '  ok  ' : '  NO '} | ${r.i18nAware ? ' ok ' : ' NO '} | ${r.hardcodedSlate}`
  );
}
const failed = report.filter((r) => !(r.platformProGone && r.brandAware && r.i18nAware));
console.log(`\n${report.length - failed.length}/${report.length} shells rebuilt brand-true`);
console.log('distinct nav arrangements: ' + new Set(report.map((r) => r.nav)).size + ', distinct hero compositions: ' + new Set(report.map((r) => r.hero)).size);
process.exitCode = failed.length ? 1 : 0;
