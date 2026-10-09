import React, { useState, useCallback } from 'react';
import {
  ArrowRight,
  Zap,
  Shield,
  TrendingUp,
  Play,
} from 'lucide-react';
import BentoGrid from '@/components/motion/BentoGrid';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import AnimatedNumber from '@/components/ui/AnimatedNumber';
import Reveal from '@/components/motion/Reveal';
import SpotlightCard from '@/components/ui/SpotlightCard';
import BorderBeam from '@/components/motion/BorderBeam';
import TiltCard from '@/components/ui/TiltCard';
import TextMorph from '@/components/motion/TextMorph';
import LazyImage from '@/components/common/LazyImage';
import BrandLogo from '@/components/common/BrandLogo';
import StaggerGroup from '@/components/motion/StaggerGroup';

export default function HeroSection({ className = '' }) {
  const [hoveredCard, setHoveredCard] = useState(null);

  const handleCardHover = useCallback((id) => setHoveredCard(id), []);
  const handleCardLeave = useCallback(() => setHoveredCard(null), []);

  return (
    <section
      className={`relative overflow-hidden bg-background min-h-screen flex flex-col ${className}`}
      aria-label="Hero section"
    >
      {/* Ambient background gradient */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 lg:pt-32 lg:pb-24">
        {/* Top bar */}
        <Reveal delay={0} direction="up">
          <div className="flex items-center justify-between mb-12">
            <BrandLogo size="md" />
            <Badge variant="outline" size="sm" dot>
              <Zap className="w-3 h-3 mr-1.5" aria-hidden="true" />
              ATS Scoring Live
            </Badge>
          </div>
        </Reveal>

        {/* Headline */}
        <Reveal delay={100} direction="up">
          <div className="text-center max-w-4xl mx-auto mb-16">
            <h1 className="font-display text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight text-foreground leading-[1.1]">
              Your next role is
              <br />
              <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
                one resume away
              </span>
              <br />
              before you apply
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              ResuPro writes resumes that pass applicant tracking systems, then
              coaches you through the interviews that follow.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button
                variant="primary"
                size="lg"
                rightIcon={<ArrowRight className="w-4 h-4" aria-hidden="true" />}
                animate
              >
                Build My Resume
              </Button>
              <Button
                variant="outline"
                size="lg"
                leftIcon={<Play className="w-4 h-4" aria-hidden="true" />}
                animate
                animationDelay={100}
              >
                Watch Demo
              </Button>
            </div>
          </div>
        </Reveal>

        {/* Bento Grid */}
        <StaggerGroup className="w-full">
          <BentoGrid columns={2} md={3} lg={4} gap={4}>
            {/* Large product showcase card */}
            <Reveal delay={0} direction="up" className="col-span-2 row-span-2">
              <SpotlightCard
                className="h-full min-h-[400px] rounded-2xl overflow-hidden group"
                interactive
                spotlight
                radius={400}
              >
                <div className="relative h-full flex flex-col">
                  <LazyImage
                    src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&auto=format&fit=crop&q=80"
                    alt="Tailored resume preview scored against a job description"
                    className="absolute inset-0 w-full h-full object-cover rounded-2xl"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/40 to-transparent rounded-2xl" />
                  <div className="relative z-10 mt-auto p-6">
                    <Badge variant="success" size="sm" className="mb-3">
                      <TrendingUp className="w-3 h-3 mr-1" aria-hidden="true" />
                      92% Match Score
                    </Badge>
                    <h3 className="text-xl font-semibold text-foreground mb-1">
                      Resume, tailored to the role
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Every line rewritten against the job description you are targeting.
                    </p>
                  </div>
                </div>
              </SpotlightCard>
            </Reveal>

            {/* Stats card */}
            <Reveal delay={100} direction="up">
              <Card
                className="h-full min-h-[200px] rounded-2xl p-6 hover:-translate-y-1 transition-all duration-200"
                hoverable
                onMouseEnter={() => handleCardHover('stats')}
                onMouseLeave={handleCardLeave}
              >
                <div className="flex flex-col h-full justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <TrendingUp className="w-4 h-4 text-primary" aria-hidden="true" />
                      </div>
                      <span className="text-sm font-medium text-muted-foreground">
                        Interviews Won
                      </span>
                    </div>
                    <div className="mt-4 flex items-baseline gap-2">
                      <AnimatedNumber
                        value={248}
                        suffix="k"
                        className="text-4xl font-bold text-foreground"
                      />
                      <span className="text-sm text-muted-foreground">this month</span>
                    </div>
                  </div>
                </div>
              </Card>
            </Reveal>

            {/* Match score */}
            <Reveal delay={200} direction="up">
              <Card
                className="h-full min-h-[200px] rounded-2xl p-6 hover:-translate-y-1 transition-all duration-200"
                hoverable
                onMouseEnter={() => handleCardHover('score')}
                onMouseLeave={handleCardLeave}
              >
                <div className="flex h-full flex-col justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Zap className="w-4 h-4 text-primary" aria-hidden="true" />
                    </div>
                    <span className="text-sm font-medium text-muted-foreground">
                      Match Score
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <AnimatedNumber
                      value={92}
                      suffix="%"
                      className="text-4xl font-bold text-foreground"
                    />
                    <span className="text-sm text-muted-foreground">average</span>
                  </div>
                </div>
              </Card>
            </Reveal>

            {/* Privacy */}
            <Reveal delay={300} direction="up">
              <Card className="h-full min-h-[200px] rounded-2xl p-6" hoverable>
                <div className="flex h-full flex-col justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Shield className="w-4 h-4 text-primary" aria-hidden="true" />
                    </div>
                    <span className="text-sm font-medium text-muted-foreground">
                      Privacy First
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Your documents stay yours. Nothing is shared with employers
                    or third parties.
                  </p>
                </div>
              </Card>
            </Reveal>
          </BentoGrid>
        </StaggerGroup>
      </div>
    </section>
  );
}
