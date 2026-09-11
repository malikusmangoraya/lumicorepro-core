import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Zap,
  Brain,
  ShoppingCart,
  LayoutDashboard,
  Shield,
  Star,
  CheckCircle2,
  Code2,
  Rocket,
  Globe,
  ChevronRight,
  Play,
} from 'lucide-react';
import { Badge, Button, ButtonMotion, Card } from '@/components/ui';
import Reveal from '@/components/motion/Reveal';
import { StaggerContainer, StaggerItem } from '@/components/motion/StaggerGroup';
import SEO, { schemas, hreflangFor } from '@/components/common/SEO';
import { cn } from '@/utils';

const Hero3DScene = React.lazy(() => import('@/components/motion/HeroCanvas'));
const Hero3DFallback = () => (
  <div
    className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 via-primary/10 to-violet-500/20"
    aria-hidden="true"
  />
);

function Hero3DBackground() {
  const ref = useRef(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => setActive(entry.isIntersecting), {
      threshold: 0.1,
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const handlePointerMove = useCallback((e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 2;
    const y = (e.clientY / window.innerHeight - 0.5) * 2;
    document.documentElement.style.setProperty('--mouse-x', String(x));
    document.documentElement.style.setProperty('--mouse-y', String(y));
  }, []);

  if (!active) {
    return (
      <div ref={ref} className="pointer-events-none absolute inset-0 z-0" aria-hidden="true" />
    );
  }

  return (
    <div
      ref={ref}
      className="pointer-events-none absolute inset-0 z-0"
      onPointerMove={handlePointerMove}
      aria-hidden="true"
    >
      <Suspense fallback={<Hero3DFallback />}>
        <Hero3DScene />
      </Suspense>
    </div>
  );
}

function useCounter(target, duration = 1800, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration, start]);
  return count;
}

const STATS = [
  { value: 60, suffix: '+', label: 'home.stats.templates', icon: '🎨' },
  { value: 12, suffix: '', label: 'home.stats.verticals', icon: '🏭' },
  { value: 9, suffix: '', label: 'home.stats.pipeline', icon: '🤖' },
  { value: 95, suffix: '%', label: 'home.stats.savings', icon: '⚡' },
];

function StatsSection({ t }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setVisible(true);
      },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const c0 = useCounter(STATS[0].value, 1400, visible);
  const c1 = useCounter(STATS[1].value, 1200, visible);
  const c2 = useCounter(STATS[2].value, 1000, visible);
  const c3 = useCounter(STATS[3].value, 1600, visible);
  const counts = [c0, c1, c2, c3];

  return (
    <Reveal>
      <div ref={ref} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {STATS.map((s, i) => (
          <Card
            key={i}
            className={cn(
              'backdrop-blur p-5 text-center transition-all duration-700',
              visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
            )}
            style={{ transitionDelay: `${i * 120}ms` }}
          >
            <div className="text-3xl mb-2">{s.icon}</div>
            <p className="font-display text-3xl font-bold text-primary">
              {counts[i]}
              {s.suffix}
            </p>
            <p className="text-xs text-muted-foreground mt-1 font-medium">{t(s.label)}</p>
          </Card>
        ))}
      </div>
    </Reveal>
  );
}

const FEATURES = [
  {
    icon: Brain,
    color: 'bg-violet-500/15 text-violet-400',
    title: 'home.featurePipeline',
    desc: 'home.featurePipelineDesc',
  },
  {
    icon: Zap,
    color: 'bg-amber-500/15 text-amber-400',
    title: 'home.featureTokens',
    desc: 'home.featureTokensDesc',
  },
  {
    icon: Code2,
    color: 'bg-blue-500/15 text-blue-400',
    title: 'home.featureDeps',
    desc: 'home.featureDepsDesc',
  },
  {
    icon: Shield,
    color: 'bg-emerald-500/15 text-emerald-400',
    title: 'home.featureSecurity',
    desc: 'home.featureSecurityDesc',
  },
  {
    icon: Globe,
    color: 'bg-sky-500/15 text-sky-400',
    title: 'home.featureVerticals',
    desc: 'home.featureVerticalsDesc',
  },
  {
    icon: Rocket,
    color: 'bg-pink-500/15 text-pink-400',
    title: 'home.featureZip',
    desc: 'home.featureZipDesc',
  },
];

const SHOWCASE = [
  {
    icon: '🍽️',
    label: 'layout.restaurant',
    path: '/templates/restaurant/RestaurantMenu',
    color: 'from-orange-500/20 to-amber-500/10',
  },
  {
    icon: '🏠',
    label: 'layout.realEstate',
    path: '/templates/realestate/PropertyListing',
    color: 'from-indigo-500/20 to-blue-500/10',
  },
  {
    icon: '🏥',
    label: 'layout.healthcare',
    path: '/templates/healthcare/MedicalPortal',
    color: 'from-rose-500/20 to-pink-500/10',
  },
  {
    icon: '💪',
    label: 'layout.fitness',
    path: '/templates/fitness/GymLanding',
    color: 'from-red-500/20 to-orange-500/10',
  },
  {
    icon: '🎓',
    label: 'layout.education',
    path: '/templates/education/CourseCatalog',
    color: 'from-violet-500/20 to-purple-500/10',
  },
  {
    icon: '✈️',
    label: 'layout.travel',
    path: '/templates/travel/TravelAgency',
    color: 'from-sky-500/20 to-cyan-500/10',
  },
  {
    icon: '👨‍💻',
    label: 'layout.portfolio',
    path: '/templates/portfolio/PersonalPortfolio',
    color: 'from-teal-500/20 to-emerald-500/10',
  },
  {
    icon: '🎨',
    label: 'layout.creative',
    path: '/templates/creative/CreativeStudio',
    color: 'from-pink-500/20 to-rose-500/10',
  },
];

const PHASES = [
  { num: '01', title: 'home.phaseMarket', desc: 'home.phaseMarketDesc' },
  { num: '02', title: 'home.phaseRequirement', desc: 'home.phaseRequirementDesc' },
  { num: '03', title: 'home.phaseStack', desc: 'home.phaseStackDesc' },
  { num: '04', title: 'home.phaseTrending', desc: 'home.phaseTrendingDesc' },
  { num: '05', title: 'home.phaseAssembly', desc: 'home.phaseAssemblyDesc' },
  { num: '06', title: 'home.phaseCode', desc: 'home.phaseCodeDesc' },
  { num: '07', title: 'home.phaseQuality', desc: 'home.phaseQualityDesc' },
  { num: '08', title: 'home.phaseImprovement', desc: 'home.phaseImprovementDesc' },
  { num: '09', title: 'home.phaseBenchmark', desc: 'home.phaseBenchmarkDesc' },
  { num: '10', title: 'home.phaseIntl', desc: 'home.phaseIntlDesc' },
  { num: '11', title: 'home.phaseI18n', desc: 'home.phaseI18nDesc' },
  { num: '12', title: 'home.phaseCompliance', desc: 'home.phaseComplianceDesc' },
  { num: '13', title: 'home.phaseSeo', desc: 'home.phaseSeoDesc' },
  { num: '14', title: 'home.phaseGrowth', desc: 'home.phaseGrowthDesc' },
  { num: '15', title: 'home.phaseDeploy', desc: 'home.phaseDeployDesc' },
];

const TESTIMONIALS = [
  { name: 'testimonial1Name', role: 'testimonial1Role', text: 'testimonial1Text', stars: 5 },
  { name: 'testimonial2Name', role: 'testimonial2Role', text: 'testimonial2Text', stars: 5 },
  { name: 'testimonial3Name', role: 'testimonial3Role', text: 'testimonial3Text', stars: 5 },
];

export default function Home() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <div className="-mx-4 -my-8 sm:-mx-6 lg:-mx-8 animate-page-enter">
      <SEO
        title={`${t('home.heroTitleA')} — LumicorePro`}
        description={t('home.heroDescription')}
        hreflang={typeof window !== 'undefined' ? hreflangFor(window.location.pathname, window.location.origin) : null}
        schema={[
          schemas.website({
            name: 'LumicorePro',
            url: typeof window !== 'undefined' ? window.location.origin : '',
          }),
          schemas.softwareApp({
            name: 'LumicorePro',
            description: t('home.heroDescription'),
            url: typeof window !== 'undefined' ? window.location.href : '',
          }),
        ]}
      />

      {/* HERO */}
      <section className="relative overflow-hidden px-4 sm:px-6 lg:px-8 pt-16 pb-20">
        <Hero3DBackground />
        <div className="pointer-events-none absolute inset-0 bg-gradient-mesh" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.12),transparent_60%)]" />

        <div className="pointer-events-none absolute top-20 left-[10%] h-64 w-64 rounded-full bg-primary/5 blur-3xl animate-float-slow" />
        <div className="pointer-events-none absolute bottom-10 right-[8%] h-80 w-80 rounded-full bg-violet-500/5 blur-3xl animate-float" />

        <div className="relative max-w-4xl mx-auto text-center">
          <Reveal delay={0} direction="up">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary mb-6">
              <Sparkles className="h-3.5 w-3.5 animate-soft-pulse" />
              <span>{t('home.heroBadge')}</span>
            </div>
          </Reveal>

          <Reveal delay={0.1} direction="up">
            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05]">
              {t('home.heroTitleA')}
              <br />
              <span className="bg-gradient-to-r from-primary via-cyan-400 to-violet-400 bg-clip-text text-transparent">
                {t('home.heroTitleB')}
              </span>
            </h1>
          </Reveal>

          <Reveal delay={0.2} direction="up">
            <p className="mt-6 max-w-2xl mx-auto text-lg text-muted-foreground leading-relaxed">
              {t('home.heroDescription')}
            </p>
          </Reveal>

          <Reveal delay={0.3} direction="up">
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <ButtonMotion
                variant="primary"
                size="xl"
                leftIcon={Sparkles}
                rightIcon={ArrowRight}
                onClick={() => navigate('/generate')}
              >
                {t('home.ctaGenerateFree')}
              </ButtonMotion>
              <Button
                variant="outline"
                size="xl"
                leftIcon={Play}
                onClick={() => navigate('/templates')}
              >
                {t('home.ctaBrowseTemplates')}
              </Button>
            </div>
          </Reveal>

          <Reveal delay={0.4} direction="up">
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
              {[t('home.trustNoCard'), t('home.trustOffline'), t('home.trustModels')].map(
                (trust, i) => (
                  <span key={i} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    {trust}
                  </span>
                )
              )}
            </div>
          </Reveal>
        </div>
      </section>

      {/* STATS */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-4xl mx-auto">
          <StatsSection t={t} />
        </div>
      </section>

      {/* TEMPLATE SHOWCASE */}
      <Reveal>
        <section className="px-4 sm:px-6 lg:px-8 pb-20 border-t border-border/50 pt-16">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-10">
              <Badge variant="secondary" className="mb-3">
                {t('home.showcaseBadge')}
              </Badge>
              <h2 className="font-display text-3xl sm:text-4xl font-bold">
                {t('home.showcaseTitle')}
              </h2>
              <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
                {t('home.showcaseDescription')}
              </p>
            </div>

            <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              {[
                {
                  icon: LayoutDashboard,
                  label: t('home.categoryDashboard'),
                  path: '/templates/dashboard/DashboardOverview',
                  color: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
                },
                {
                  icon: ShoppingCart,
                  label: t('home.categoryEcommerce'),
                  path: '/templates/ecommerce/ProductListing',
                  color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
                },
                {
                  icon: Brain,
                  label: t('home.categoryAI'),
                  path: '/templates/ai/ChatInterface',
                  color: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
                },
                {
                  icon: Globe,
                  label: t('home.categoryBusiness'),
                  path: '/templates/business/LandingPage',
                  color: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                },
              ].map((c, i) => {
                const Icon = c.icon;
                return (
                  <StaggerItem key={i}>
                    <Button
                      variant="outline"
                      fullWidth
                      onClick={() => navigate(c.path)}
                      className="group flex items-center gap-3 rounded-xl p-4 hover:shadow-card-hover transition-all duration-200 bg-card hover:border-primary/30 justify-start h-auto"
                    >
                      <span
                        className={cn(
                          'h-9 w-9 rounded-lg flex items-center justify-center border shrink-0',
                          c.color
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="text-sm font-semibold group-hover:text-primary transition-colors">
                        {c.label}
                      </span>
                      <ChevronRight className="h-4 w-4 ml-auto text-muted-foreground group-hover:text-primary transition-colors" />
                    </Button>
                  </StaggerItem>
                );
              })}
            </StaggerContainer>

            <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
              {SHOWCASE.map((s, i) => (
                <StaggerItem key={i}>
                  <Button
                    variant="outline"
                    fullWidth
                    onClick={() => navigate(s.path)}
                    className={cn(
                      'group flex flex-col items-center justify-center gap-2 rounded-xl border border-border bg-gradient-to-br p-5 hover:border-primary/40 hover:shadow-card-hover transition-all duration-200 text-center h-auto',
                      s.color
                    )}
                  >
                    <span className="text-3xl group-hover:scale-110 transition-transform duration-200">
                      {s.icon}
                    </span>
                    <span className="text-sm font-semibold group-hover:text-primary transition-colors">
                      {t(s.label)}
                    </span>
                  </Button>
                </StaggerItem>
              ))}
            </StaggerContainer>

            <div className="text-center">
              <Button
                variant="outline"
                onClick={() => navigate('/templates')}
                className="rounded-xl border border-border bg-card px-6 py-3 text-sm font-semibold hover:border-primary/40 hover:text-primary transition-all"
                rightIcon={ArrowRight}
              >
                {t('home.viewAll')}
              </Button>
            </div>
          </div>
        </section>
      </Reveal>

      {/* FEATURES */}
      <Reveal>
        <section className="px-4 sm:px-6 lg:px-8 py-20 bg-card/30 border-y border-border/50">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <Badge variant="info" className="mb-3">
                {t('home.featuresBadge')}
              </Badge>
              <h2 className="font-display text-3xl sm:text-4xl font-bold">
                {t('home.featuresTitle')}
              </h2>
              <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
                {t('home.featuresDescription')}
              </p>
            </div>
            <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {FEATURES.map((f, i) => {
                const Icon = f.icon;
                return (
                  <StaggerItem key={i}>
                    <Card className="rounded-2xl border border-border bg-card p-6 hover:border-primary/30 hover:shadow-card-hover transition-all duration-200 group h-full">
                      <div
                        className={cn(
                          'h-11 w-11 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform',
                          f.color
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <h3 className="font-display font-bold mb-2">{t(f.title)}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">{t(f.desc)}</p>
                    </Card>
                  </StaggerItem>
                );
              })}
            </StaggerContainer>
          </div>
        </section>
      </Reveal>

      {/* 15-PHASE PIPELINE */}
      <Reveal>
        <section className="px-4 sm:px-6 lg:px-8 py-20">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <Badge variant="warning" className="mb-3">
                {t('home.pipelineBadge')}
              </Badge>
              <h2 className="font-display text-3xl sm:text-4xl font-bold">
                {t('home.pipelineTitle')}
              </h2>
              <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
                {t('home.pipelineDescription')}
              </p>
            </div>
            <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {PHASES.map((phase, i) => (
                <StaggerItem key={i}>
                  <Card className="relative rounded-xl border border-border bg-card/60 p-5 hover:border-primary/30 transition-all duration-200 h-full">
                    <div className="flex items-start gap-3">
                      <span className="font-mono text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded shrink-0">
                        {phase.num}
                      </span>
                      <div>
                        <h3 className="font-display font-bold text-sm">{t(phase.title)}</h3>
                        <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                          {t(phase.desc)}
                        </p>
                      </div>
                    </div>
                  </Card>
                </StaggerItem>
              ))}
            </StaggerContainer>
            <div className="text-center mt-10">
              <ButtonMotion
                variant="primary"
                size="xl"
                leftIcon={Rocket}
                rightIcon={ArrowRight}
                onClick={() => navigate('/generate')}
              >
                {t('home.tryPipeline')}
              </ButtonMotion>
            </div>
          </div>
        </section>
      </Reveal>

      {/* TESTIMONIALS */}
      <Reveal>
        <section className="px-4 sm:px-6 lg:px-8 py-20 bg-card/30 border-t border-border/50">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <Badge variant="success" className="mb-3">
                {t('home.socialBadge')}
              </Badge>
              <h2 className="font-display text-3xl font-bold">{t('home.socialTitle')}</h2>
            </div>
            <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {TESTIMONIALS.map((tst, i) => (
                <StaggerItem key={i}>
                  <Card className="rounded-2xl border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200 h-full">
                    <div className="flex gap-0.5 mb-4">
                      {Array.from({ length: tst.stars }).map((_, j) => (
                        <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-5">
                      "{t(tst.text)}"
                    </p>
                    <div className="flex items-center gap-3 pt-4 border-t border-border">
                      <div className="h-9 w-9 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary text-sm">
                        {t(tst.name).charAt(0)}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{t(tst.name)}</p>
                        <p className="text-xs text-muted-foreground">{t(tst.role)}</p>
                      </div>
                    </div>
                  </Card>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>
        </section>
      </Reveal>

      {/* CTA */}
      <Reveal>
        <section className="px-4 sm:px-6 lg:px-8 py-20">
          <div className="max-w-3xl mx-auto text-center relative">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.1),transparent_70%)]" />
            <div className="relative">
              <span className="text-5xl mb-6 block">⚡</span>
              <h2 className="font-display text-4xl sm:text-5xl font-bold mb-4">
                {t('home.ctaTitleA')}
                <br />
                <span className="bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent">
                  {t('home.ctaTitleB')}
                </span>
              </h2>
              <p className="text-muted-foreground mb-8 text-lg max-w-xl mx-auto">
                {t('home.ctaDescription')}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <ButtonMotion
                  variant="primary"
                  size="xl"
                  leftIcon={Sparkles}
                  rightIcon={ArrowRight}
                  onClick={() => navigate('/generate')}
                >
                  {t('home.ctaStartGenerating')}
                </ButtonMotion>
                <Button variant="outline" size="xl" onClick={() => navigate('/templates')}>
                  {t('home.ctaBrowseTemplates')}
                </Button>
              </div>
            </div>
          </div>
        </section>
      </Reveal>
    </div>
  );
}
