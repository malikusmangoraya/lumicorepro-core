import {
  ArrowRight,
  Zap,
  Shield,
  LayoutDashboard,
  Star,
  Users,
  Globe,
  CheckCircle2,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Button, Card, Badge } from '@/components/ui';
import { img } from '@/utils/images';

const features = [
  {
    icon: Zap,
    color: 'bg-amber-500/15 text-amber-400',
    title: 'Lightning Fast',
    text: 'Optimised for Core Web Vitals. Lighthouse 95+ out of the box.',
  },
  {
    icon: Shield,
    color: 'bg-emerald-500/15 text-emerald-400',
    title: 'Enterprise Security',
    text: 'OWASP-compliant, JWT auth, rate limiting, and encrypted sessions.',
  },
  {
    icon: LayoutDashboard,
    color: 'bg-blue-500/15 text-blue-400',
    title: 'Analytics Built-in',
    text: 'Real-time dashboards, conversion tracking, and ROI reporting.',
  },
  {
    icon: Globe,
    color: 'bg-violet-500/15 text-violet-400',
    title: 'Global CDN',
    text: 'Deploy to Vercel, AWS, or Railway. Edge-ready in minutes.',
  },
  {
    icon: Users,
    color: 'bg-rose-500/15 text-rose-400',
    title: 'Team Collaboration',
    text: 'Role-based access, audit logs, and multi-workspace support.',
  },
  {
    icon: Star,
    color: 'bg-cyan-500/15 text-cyan-400',
    title: 'Award-Winning UX',
    text: 'Designed for delight — dark mode, motion, and accessibility.',
  },
];

const logos = ['Stripe', 'Notion', 'Vercel', 'Supabase', 'Linear', 'Figma'];

export default function LandingPage() {
  return (
    <TemplateShell
      title="Landing Page"
      description="World-class SaaS landing page with hero, features, social proof, and CTA."
      category="Business"
    >
      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="relative overflow-hidden rounded-2xl border border-border mb-8">
        <img
          src={img.business.hero}
          alt="Hero"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/55 to-black/20" />
        <div className="relative px-8 py-20 text-center">
          <Badge variant="info" className="mb-4">
            🚀 Trusted by 10,000+ teams worldwide
          </Badge>
          <h2 className="font-display text-5xl sm:text-6xl font-black tracking-tight text-white leading-[1.05]">
            Ship Products
            <br />
            <span className="bg-gradient-to-r from-teal-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
              People Love
            </span>
          </h2>
          <p className="mt-5 max-w-xl mx-auto text-white/75 text-lg leading-relaxed">
            A complete React + Node.js platform — dashboards, commerce, AI, and analytics. From idea
            to production in hours, not weeks.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
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
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/50">
            {['No credit card', '14-day trial', 'Cancel anytime'].map((t) => (
              <span key={t} className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trusted by logos ──────────────────────────────────── */}
      <div className="text-center mb-10">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-4">
          Trusted by world-class teams
        </p>
        <div className="flex flex-wrap items-center justify-center gap-6">
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

      {/* ── Features ──────────────────────────────────────────── */}
      <div className="mb-10">
        <div className="text-center mb-8">
          <Badge variant="secondary" className="mb-3">
            Why teams choose us
          </Badge>
          <h3 className="font-display text-3xl font-bold">Everything you need to ship</h3>
          <p className="mt-2 text-muted-foreground max-w-lg mx-auto">
            Production-grade features out of the box — so you focus on building, not plumbing.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <Card
                key={f.title}
                className="hover-lift group"
                animate="fade-up"
                animationDelay={i * 70}
              >
                <div
                  className={`mb-4 inline-flex rounded-xl p-3 ${f.color} group-hover:scale-110 transition-transform`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <h4 className="font-display font-bold mb-2">{f.title}</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.text}</p>
              </Card>
            );
          })}
        </div>
      </div>

      {/* ── Social proof ──────────────────────────────────────── */}
      <div className="mb-10 grid grid-cols-1 md:grid-cols-3 gap-5">
        {[
          {
            name: 'Sarah Chen',
            role: 'CTO, NexSoft',
            text: 'We shipped our MVP in 3 days. The template quality is genuinely production-grade.',
            stars: 5,
          },
          {
            name: 'James Park',
            role: 'Founder, Launchly',
            text: 'Replaced 6 weeks of setup with a single generation prompt. Absolutely game-changing.',
            stars: 5,
          },
          {
            name: 'Aisha Malik',
            role: 'Lead Dev, FastStack',
            text: "The agent understands Urdu prompts too. Built our Pakistani startup's site in minutes.",
            stars: 5,
          },
        ].map((t, i) => (
          <Card key={i} animate="fade-up" animationDelay={i * 80} className="hover-lift">
            <div className="flex gap-0.5 mb-4">
              {Array.from({ length: t.stars }).map((_, j) => (
                <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
              ))}
            </div>
            <p className="text-sm text-muted-foreground italic mb-5">"{t.text}"</p>
            <div className="flex items-center gap-3 pt-4 border-t border-border">
              <div className="h-9 w-9 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary text-sm">
                {t.name.charAt(0)}
              </div>
              <div>
                <p className="font-semibold text-sm">{t.name}</p>
                <p className="text-xs text-muted-foreground">{t.role}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* ── CTA Banner ────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 via-cyan-500/5 to-transparent p-10 text-center">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.12),transparent_65%)]" />
        <div className="relative">
          <h3 className="font-display text-3xl font-bold mb-3">Start Building Today</h3>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            Join thousands of teams shipping faster with production-grade, ready-to-launch templates.
          </p>
          <Button size="lg" rightIcon={ArrowRight} className="shadow-glow hover:shadow-glow-lg">
            Get started free →
          </Button>
        </div>
      </div>
    </TemplateShell>
  );
}
