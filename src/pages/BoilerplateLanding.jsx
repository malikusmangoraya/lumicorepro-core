import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCurrency } from '@/hooks/useCurrency';
import {
  BarChart3,
  Shield,
  Bell,
  UserPlus,
  Moon,
  CheckCircle2,
  ArrowRight,
  Zap,
  Settings,
  FileText,
  Lock,
  Globe,
} from 'lucide-react';
import { BrandLogo } from '@/components/common';
import { Button } from '@/components/ui';
import SkipToContent from '@/components/common/SkipToContent';

const plans = [
  {
    name: 'Starter',
    nameKey: 'pricing.starter',
    price: 49,
    priceKey: 'pricing.starterPrice',
    desc: 'pricing.starterDesc',
    features: [
      'pricing.feat1',
      'pricing.feat2',
      'pricing.feat3',
      'pricing.feat5',
    ],
    cta: 'pricing.getStarter',
    popular: false,
  },
  {
    name: 'Pro',
    nameKey: 'pricing.pro',
    price: 99,
    priceKey: 'pricing.proPrice',
    desc: 'pricing.proDesc',
    features: [
      'pricing.feat1',
      'pricing.feat2',
      'pricing.feat3',
      'pricing.feat4',
      'pricing.feat5',
      'pricing.feat6',
    ],
    cta: 'pricing.getPro',
    popular: true,
  },
  {
    name: 'Enterprise',
    nameKey: 'pricing.enterprise',
    price: 199,
    priceKey: 'pricing.enterprisePrice',
    desc: 'pricing.enterpriseDesc',
    features: [
      'pricing.feat1',
      'pricing.feat2',
      'pricing.feat3',
      'pricing.feat4',
      'pricing.feat5',
      'pricing.feat6',
      'pricing.feat7',
    ],
    cta: 'pricing.getEnterprise',
    popular: false,
  },
];

const features = [
  { icon: BarChart3, key: 'usageLimiter', label: 'usageLimiter.title', desc: 'usageLimiter.desc' },
  { icon: Settings, key: 'onboarding', label: 'onboarding.title', desc: 'onboarding.desc' },
  { icon: FileText, key: 'auditLog', label: 'auditLog.title', desc: 'auditLog.desc' },
  { icon: Bell, key: 'notifCenter', label: 'notifCenter.title', desc: 'notifCenter.desc' },
  { icon: UserPlus, key: 'inviteSystem', label: 'inviteSystem.title', desc: 'inviteSystem.desc' },
  { icon: Moon, key: 'darkMode', label: 'darkMode.title', desc: 'darkMode.desc' },
];

const steps = [
  { icon: Zap, key: 'step1', label: 'step1.title', desc: 'step1.desc' },
  { icon: Settings, key: 'step2', label: 'step2.title', desc: 'step2.desc' },
  { icon: Globe, key: 'step3', label: 'step3.title', desc: 'step3.desc' },
];

const faqs = [
  { qKey: 'faq.q1', aKey: 'faq.a1' },
  { qKey: 'faq.q2', aKey: 'faq.a2' },
  { qKey: 'faq.q3', aKey: 'faq.a3' },
];

const SectionHeading = ({ children, sub }) => (
  <div className="text-center max-w-2xl mx-auto mb-12">
    <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
      {children}
    </h2>
    {sub && (
      <p className="mt-4 text-lg text-muted-foreground">{sub}</p>
    )}
  </div>
);

export default function BoilerplateLanding() {
  const { t } = useTranslation();
  const { formatPrice } = useCurrency();

  return (
    <>
      <SkipToContent />

      <section
        id="hero"
        className="relative isolate overflow-hidden bg-background px-4 py-24 sm:py-32"
      >
        <div className="mx-auto max-w-5xl text-center">
          <div className="mb-8 flex justify-center">
            <BrandLogo variant="full" size="lg" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-6xl">
            {t('landing.heroTitle', 'Ship your SaaS in days, not months')}
          </h1>
          <p className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto">
            {t(
              'landing.heroSub',
              'Authentication, billing, user management, notifications — everything wired and production-ready. Just add your product.'
            )}
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button asChild variant="primary" size="lg" leftIcon={ArrowRight}>
              <Link to="/register">{t('landing.heroCta', 'Get Started Free')}</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/boilerplate#features">{t('landing.heroSecondary', 'See Features')}</Link>
            </Button>
          </div>
          <div className="mt-16 grid grid-cols-2 gap-6 sm:grid-cols-4 max-w-lg mx-auto">
            {[
              ['landing.stat1', '500+'],
              ['landing.stat2', '99.9%'],
              ['landing.stat3', '<150 KB'],
              ['landing.stat4', '13'],
            ].map(([key, fallback]) => (
              <div key={key} className="text-center">
                <p className="text-2xl font-bold text-primary">{t(key, fallback)}</p>
                <p className="mt-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  {t(key + '.label', key === 'landing.stat1' ? 'Users Served' : key === 'landing.stat2' ? 'Uptime' : key === 'landing.stat3' ? 'JS Bundle' : 'Languages')}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="bg-muted/40 py-24 sm:py-32">
        <div className="mx-auto max-w-6xl px-4">
          <SectionHeading
            sub={t(
              'landing.featuresSub',
              'Six enterprise-grade capabilities that most boilerplates leave out.'
            )}
          >
            {t('landing.featuresTitle', 'Built-in features that set you apart')}
          </SectionHeading>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.key}
                  className="rounded-2xl border border-border bg-card p-8 transition-all duration-200 hover:shadow-lg hover:-translate-y-1"
                >
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {t(f.label, f.key)}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {t(f.desc, '')}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section id="how" className="py-24 sm:py-32">
        <div className="mx-auto max-w-5xl px-4">
          <SectionHeading
            sub={t('landing.howSub', 'From idea to production in three deliberate steps.')}
          >
            {t('landing.howTitle', 'How it works')}
          </SectionHeading>
          <ol className="relative mt-16 grid gap-12 sm:grid-cols-3 list-none p-0">
            {steps.map((s, i) => {
              const Icon = s.icon;
              return (
                <li key={s.key} className="relative text-center">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-xl font-bold">
                    {i + 1}
                  </div>
                  <div className="mt-4 flex justify-center text-primary">
                    <Icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-foreground">
                    {t(s.label, s.key)}
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {t(s.desc, '')}
                  </p>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      <section id="pricing" className="bg-muted/40 py-24 sm:py-32">
        <div className="mx-auto max-w-6xl px-4">
          <SectionHeading
            sub={t('landing.pricingSub', 'Simple, predictable pricing. Scale when you are ready.')}
          >
            {t('landing.pricingTitle', 'Choose your plan')}
          </SectionHeading>
          <div className="mt-16 grid gap-8 lg:grid-cols-3 items-start">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border bg-card p-8 transition-all duration-200 ${
                  plan.popular
                    ? 'border-primary shadow-lg ring-2 ring-primary/20 scale-105 z-10'
                    : 'border-border hover:shadow-md'
                }`}
              >
                {plan.popular && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-semibold text-primary-foreground">
                    {t('pricing.popular', 'Most Popular')}
                  </span>
                )}
                <h3 className="text-xl font-bold text-foreground">{t(plan.nameKey, plan.name)}</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {t(plan.desc, '')}
                </p>
                <div className="mt-6 flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold text-foreground">
                    {formatPrice(plan.price)}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    /{t('pricing.month', 'mo')}
                  </span>
                </div>
                <ul className="mt-8 space-y-3">
                  {plan.features.map((fk) => (
                    <li key={fk} className="flex items-start gap-3 text-sm text-muted-foreground">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden="true" />
                      <span>{t(fk, fk)}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  asChild
                  variant={plan.popular ? 'primary' : 'outline'}
                  size="lg"
                  fullWidth
                  className="mt-8"
                >
                  <Link to="/register">{t(plan.cta, plan.name)}</Link>
                </Button>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="py-24 sm:py-32">
        <div className="mx-auto max-w-3xl px-4">
          <SectionHeading>{t('landing.faqTitle', 'Frequently asked questions')}</SectionHeading>
          <dl className="mt-12 space-y-6">
            {faqs.map((faq, i) => (
              <details
                key={i}
                className="group rounded-2xl border border-border bg-card p-6"
              >
                <summary className="flex cursor-pointer items-center justify-between gap-4 text-base font-semibold text-foreground">
                  <span>{t(faq.qKey, '')}</span>
                  <span className="shrink-0 text-muted-foreground transition-transform duration-200 group-open:rotate-180">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </summary>
                <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                  {t(faq.aKey, '')}
                </p>
              </details>
            ))}
          </dl>
        </div>
      </section>

      <section className="bg-primary py-20 sm:py-24">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-primary-foreground sm:text-4xl">
            {t('landing.ctaTitle', 'Ready to launch?')}
          </h2>
          <p className="mt-4 text-lg text-primary-foreground/80 max-w-xl mx-auto">
            {t(
              'landing.ctaSub',
              'Join thousands of teams shipping better products faster.'
            )}
          </p>
          <Button
            asChild
            variant="secondary"
            size="lg"
            leftIcon={Lock}
            className="mt-8 bg-white text-primary hover:bg-white/90"
          >
            <Link to="/register">{t('landing.ctaCta', 'Start building now')}</Link>
          </Button>
        </div>
      </section>
    </>
  );
}