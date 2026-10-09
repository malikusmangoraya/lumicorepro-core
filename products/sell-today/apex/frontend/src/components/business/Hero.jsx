/**
 * Hero — the page-opening composition for this product.
 *
 * Variant: split-metric. Copy comes from the caller or from i18n, and every colour is a
 * --t-* token, so the same primitive renders differently for each brand rather than being one
 * hard-coded dark template shared by every product.
 *
 * The artwork is a real asset that ships with this product and is imported so the bundler
 * fingerprints it. (The previous version imported `img` from utils.js, which never exported
 * it — a latent build failure for anything that wired this component up.)
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight, PlayCircle, Sparkles } from 'lucide-react';
import LazyImage from '../common/LazyImage';
import defaultImage from '../../assets/images/strategy.jpg';
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
  imageAlt = 'Team reviewing growth plans',
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
        {badge || t('hero.badge', 'Conversion engineering')}
      </span>
    );

  const renderActions = () => (
    <div className="mt-8 flex flex-col gap-3 sm:flex-row">
      <button type="button" onClick={onPrimary} className="btn-primary justify-center">
        {primaryLabel || t('hero.primary', 'Start free')}
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
        <div className="grid items-center gap-12 lg:grid-cols-2">
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
        </div>
      </div>
    </section>
  );
};

export default Hero;
