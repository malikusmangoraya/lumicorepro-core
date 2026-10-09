import {
  ArrowRight,
  Zap,
  Shield,
  LayoutDashboard,
  Star,
  Users,
  Globe,
  CheckCircle2,
  Truck,
  RotateCcw,
  Headphones,
  Lock,
  BarChart2,
  Code,
  Layers,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import {
  Button,
  Card,
  Badge,
  StatsCard,
  FeatureCard,
  PricingCard,
  ScrollReveal,
  StaggerContainer,
  GlassButton,
} from '@/components/ui';
import { features, testimonials, logos, stats, pricingPlans } from './data/mockData';
import { img } from '@/utils/images';
import { cn } from '@/utils';

const iconMap = {
  Zap,
  Shield,
  LayoutDashboard,
  Globe,
  Users,
  Star,
  Truck,
  RotateCcw,
  Headphones,
  Lock,
  BarChart2,
  Code,
  Layers,
};

export default function LandingPage() {
  return (
    <TemplateShell
      title="Landing Page"
      description="World-class SaaS landing page with hero, features, social proof, and pricing."
      category="Business"
    >
      {/* ── Hero ──────────────────────────────────────────────── */}
      <ScrollReveal animate="fade-up">
        <section className="relative overflow-hidden rounded-3xl border border-border mb-12">
          <img
            src={img.business.hero}
            alt="Hero background"
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
            decoding="async"
            fetchPriority="high"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/55 to-black/20" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.15),transparent_70%)]" />
          <div className="relative px-8 py-24 md:py-32 text-center">
            <Badge variant="info" className="mb-6 inline-block animate-fade-in-up">
              <span className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                🚀 Trusted by 10,000+ teams worldwide
              </span>
            </Badge>
            <h2 className="font-display text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-[1.05]">
              Ship Products
              <br />
              <span className="bg-gradient-to-r from-teal-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
                People Love
              </span>
            </h2>
            <p className="mt-6 max-w-2xl mx-auto text-white/75 text-lg leading-relaxed">
              A complete React + Node.js platform — dashboards, commerce, AI, and analytics. From idea
              to production in hours, not weeks.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" rightIcon={ArrowRight} className="shadow-glow hover:shadow-glow-lg">
                Start for Free
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-white/30 text-white hover:bg-white/10 hover:border-white/50"
              >
                View Live Demo
              </Button>
            </div>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-white/60">
              {['No credit card required', '14-day free trial', 'Cancel anytime'].map((t) => (
                <span key={t} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  {t}
                </span>
              ))}
            </div>
          </div>
        </section>
      </ScrollReveal>

      {/* ── Trust Stats ────────────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.1}>
        <StaggerContainer stagger={0.1}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
            {stats.map((stat, i) => (
              <ScrollReveal key={stat.label} animate="none">
                <StatsCard
                  title={stat.label}
                  value={stat.value}
                  icon={Users}
                  iconColor="primary"
                  variant="glass"
                  className="text-center py-8"
                />
              </ScrollReveal>
            ))}
          </div>
        </StaggerContainer>
      </ScrollReveal>

      {/* ── Trusted by logos ──────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.2}>
        <div className="text-center mb-12">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-4">
            Trusted by world-class teams
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 opacity-60 hover:opacity-100 transition-opacity">
            {logos.map((name) => (
              <span
                key={name}
                className="font-display font-bold text-lg text-muted-foreground/50 hover:text-muted-foreground transition-colors"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      </ScrollReveal>

      {/* ── Features ──────────────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.3}>
        <div className="mb-12">
          <div className="text-center mb-10">
            <Badge variant="secondary" className="mb-3">
              Why teams choose us
            </Badge>
            <h3 className="font-display text-3xl sm:text-4xl font-bold">Everything you need to ship</h3>
            <p className="mt-3 text-muted-foreground max-w-lg mx-auto">
              Production-grade features out of the box — so you focus on building, not plumbing.
            </p>
          </div>
          <StaggerContainer stagger={0.08}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {features.map((f, i) => {
                const Icon = iconMap[f.icon];
                return (
                  <ScrollReveal key={f.title} animate="none">
                    <FeatureCard
                      title={f.title}
                      description={f.text}
                      icon={Icon}
                      iconColor={f.color}
                      variant="default"
                      badge={i === 0 ? 'New' : undefined}
                    />
                  </ScrollReveal>
                );
              })}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>

      {/* ── Feature Highlights ────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.4}>
        <div className="mb-12">
          <div className="text-center mb-10">
            <Badge variant="secondary" className="mb-3">
              Platform highlights
            </Badge>
            <h3 className="font-display text-3xl sm:text-4xl font-bold">Built for modern development</h3>
            <p className="mt-3 text-muted-foreground max-w-lg mx-auto">
              Every feature is designed to accelerate your workflow and delight your users.
            </p>
          </div>
          <StaggerContainer stagger={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  icon: Lock,
                  iconColor: 'violet',
                  title: 'Enterprise Security',
                  description: 'SOC 2 compliant, end-to-end encryption, advanced RBAC, and audit logging.',
                  features: ['SSO/SAML', '2FA', 'Audit logs', 'Data residency'],
                },
                {
                  icon: BarChart2,
                  iconColor: 'cyan',
                  title: 'Real-time Analytics',
                  description: 'Track metrics that matter with customizable dashboards and automated reports.',
                  features: ['Custom dashboards', 'Funnel analysis', 'Cohort retention', 'Export API'],
                },
                {
                  icon: Code,
                  iconColor: 'amber',
                  title: 'Developer Experience',
                  description: 'Type-safe APIs, hot reload, component library, and comprehensive documentation.',
                  features: ['TypeScript', 'Storybook', 'CLI tools', 'VS Code extension'],
                },
              ].map((f, i) => (
                <ScrollReveal key={f.title} animate="none">
                  <FeatureCard
                    title={f.title}
                    description={f.description}
                    icon={iconMap[f.icon]}
                    iconColor={f.iconColor}
                    iconSize="lg"
                    variant="glass"
                    className="p-8"
                  >
                    <ul className="space-y-2" role="list">
                      {f.features.map((feat) => (
                        <li key={feat} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          {feat}
                        </li>
                      ))}
                    </ul>
                  </FeatureCard>
                </ScrollReveal>
              ))}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>

      {/* ── Social proof ──────────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.5}>
        <div className="mb-12">
          <div className="text-center mb-10">
            <Badge variant="secondary" className="mb-3">
              Customer stories
            </Badge>
            <h3 className="font-display text-3xl sm:text-4xl font-bold">Loved by developers everywhere</h3>
            <p className="mt-3 text-muted-foreground max-w-lg mx-auto">
              See what teams are building with our platform.
            </p>
          </div>
          <StaggerContainer stagger={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {testimonials.map((t, i) => (
                <ScrollReveal key={i} animate="none">
                  <Card animate="none" className="hover-lift h-full">
                    <div className="flex gap-0.5 mb-4">
                      {Array.from({ length: t.stars }).map((_, j) => (
                        <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground italic mb-6">"{t.text}"</p>
                    <div className="flex items-center gap-3 pt-4 border-t border-border">
                      <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary text-sm">
                        {t.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{t.name}</p>
                        <p className="text-xs text-muted-foreground">{t.role}</p>
                      </div>
                    </div>
                  </Card>
                </ScrollReveal>
              ))}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>

      {/* ── Pricing ───────────────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.6}>
        <div className="mb-12">
          <div className="text-center mb-10">
            <Badge variant="secondary" className="mb-3">
              Simple, transparent pricing
            </Badge>
            <h3 className="font-display text-3xl sm:text-4xl font-bold">Start free, scale as you grow</h3>
            <p className="mt-3 text-muted-foreground max-w-lg mx-auto">
              No hidden fees. Cancel anytime. All plans include a 14-day free trial.
            </p>
          </div>
          <StaggerContainer stagger={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {pricingPlans.map((plan, i) => (
                <ScrollReveal key={plan.name} animate="none">
                  <PricingCard
                    name={plan.name}
                    price={plan.price}
                    period={plan.period}
                    description={plan.description}
                    features={plan.features}
                    ctaText={plan.ctaText}
                    ctaVariant={plan.ctaVariant}
                    highlighted={plan.highlighted}
                    badge={plan.badge}
                  />
                </ScrollReveal>
              ))}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>

      {/* ── CTA Banner ────────────────────────────────────────── */}
      <ScrollReveal animate="fade-up" delay={0.7}>
        <div className="relative overflow-hidden rounded-3xl border border-primary/30 bg-gradient-to-br from-primary/10 via-cyan-500/5 to-transparent p-8 md:p-12 text-center">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.12),transparent_65%)]" />
          <div className="relative">
            <Badge variant="info" className="mb-4 inline-block">
              Ready to get started?
            </Badge>
            <h3 className="font-display text-3xl sm:text-4xl font-bold mb-4">Start Building Today</h3>
            <p className="text-muted-foreground mb-8 max-w-md mx-auto">
              Join thousands of teams shipping faster with production-grade, ready-to-launch templates.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" rightIcon={ArrowRight} className="shadow-glow hover:shadow-glow-lg">
                Get started free →
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-white/30 text-white hover:bg-white/10 hover:border-white/50"
              >
                Schedule a Demo
              </Button>
            </div>
          </div>
        </div>
      </ScrollReveal>
    </TemplateShell>
  );
}