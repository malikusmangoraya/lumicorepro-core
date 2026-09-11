import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink, Layers, MapPin, TrendingUp, CheckCircle2 } from 'lucide-react';
import { Card, Badge, Button } from '@/components/ui';
import Reveal from '@/components/motion/Reveal';
import { StaggerContainer, StaggerItem } from '@/components/motion/StaggerGroup';
import SEO from '@/components/common/SEO';
import { cn } from '@/utils';
import caseStudies from '@/data/caseStudies';

const INDUSTRY_FILTERS = ['all', ...new Set(caseStudies.map((s) => s.industry))];

export default function Gallery() {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('all');

  const visible = filter === 'all' ? caseStudies : caseStudies.filter((s) => s.industry === filter);

  return (
    <>
      <SEO
        title="Portfolio — AI-Generated Projects | LumicorePro"
        description="See real projects built with LumicorePro AI — e-commerce, healthcare, restaurants, real estate, education, and fitness platforms generated in minutes."
      />

      <section className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        {/* Header */}
        <Reveal>
          <div className="mb-14 text-center">
            <Badge variant="info" className="mb-4">Case Studies</Badge>
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
              AI-Generated <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent">Projects</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              Every project below was generated end-to-end by LumicorePro AI — from copy and code to deployment. Real results from real businesses.
            </p>
          </div>
        </Reveal>

        {/* Filter chips */}
        <Reveal delay={0.1}>
          <div className="mb-10 flex flex-wrap justify-center gap-2">
            {INDUSTRY_FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  'rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200',
                  filter === f
                    ? 'bg-primary text-primary-foreground shadow-md'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </Reveal>

        {/* Cards grid */}
        <StaggerContainer className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((study) => (
            <StaggerItem key={study.id}>
              <Card
                className={cn(
                  'group relative flex flex-col overflow-hidden border border-border/50 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1',
                  'bg-gradient-to-br',
                  study.color
                )}
              >
                {/* Top bar */}
                <div className="flex items-center justify-between px-5 pt-5">
                  <Badge variant="outline" className="text-xs">{study.industry}</Badge>
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="h-3 w-3" />
                    {study.region}
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1 px-5 pb-4 pt-3">
                  <h3 className="mb-2 text-lg font-bold leading-snug">{study.title}</h3>
                  <p className="mb-4 line-clamp-3 text-sm text-muted-foreground">{study.summary}</p>

                  {/* Stack chips */}
                  <div className="mb-4 flex flex-wrap gap-1.5">
                    {study.stack.map((s) => (
                      <span key={s} className="rounded bg-background/60 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                        {s}
                      </span>
                    ))}
                  </div>

                  {/* Metrics */}
                  <div className="mb-4 grid grid-cols-3 gap-2 rounded-lg bg-background/40 p-3">
                    {Object.entries(study.metrics).map(([key, val]) => (
                      <div key={key} className="text-center">
                        <p className="text-lg font-bold text-primary">{val}</p>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5">
                    {study.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                    ))}
                  </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between border-t border-border/40 px-5 py-3">
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                    {study.client}
                  </span>
                  <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs">
                    View Details
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </Card>
            </StaggerItem>
          ))}
        </StaggerContainer>

        {/* Empty state */}
        {visible.length === 0 && (
          <div className="py-20 text-center text-muted-foreground">
            <Layers className="mx-auto mb-3 h-10 w-10 opacity-40" />
            <p>No projects found for this filter.</p>
          </div>
        )}

        {/* CTA */}
        <Reveal delay={0.2}>
          <div className="mt-16 text-center">
            <p className="mb-4 text-muted-foreground">Ready to build your own?</p>
            <Button size="lg" onClick={() => window.location.assign('/generate')}>
              <TrendingUp className="mr-2 h-4 w-4" />
              Generate Your Project
            </Button>
          </div>
        </Reveal>
      </section>
    </>
  );
}
