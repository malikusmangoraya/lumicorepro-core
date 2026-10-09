import { useState } from 'react';
import { Link2, Mail, MapPin, ExternalLink, Briefcase, Code2, Star, GitBranch, User, X, ChevronDown } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress, StatsCard, FeatureCard, ScrollReveal, StaggerContainer, GlassButton, AvatarGroup } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { profile, skills, projects, experience, testimonials } from './data/mockData';

export default function PersonalPortfolio() {
  const [activeFilter, setActiveFilter] = useState('All');
  const filters = ['All', 'Featured'];
  const filteredProjects = activeFilter === 'Featured' ? projects.filter((p) => p.featured) : projects;

  const socialLinks = [
    { icon: GitBranch, href: `https://${profile.github}`, label: 'GitHub' },
    { icon: User, href: `https://${profile.linkedin}`, label: 'LinkedIn' },
    { icon: X, href: '#', label: 'X (Twitter)' },
    { icon: Mail, href: `mailto:${profile.email}`, label: 'Email' },
  ];

  const avatarGroupData = [
    { id: 1, name: 'Ahmed S.', src: img.people.male1 },
    { id: 2, name: 'Sara L.', src: img.people.female1 },
    { id: 3, name: 'John D.', src: img.people.male2 },
    { id: 4, name: 'Maria K.', src: img.people.female2 },
    { id: 5, name: 'Alex C.', src: img.people.male3 },
  ];

  return (
    <TemplateShell
      title="Personal Portfolio"
      description="Full-stack developer portfolio with skills, projects, experience, and testimonials."
      category="Portfolio"
      actions={
        <div className="flex gap-2">
          <Button size="sm" variant="outline">
            <Mail className="h-4 w-4 mr-1" />
            Contact
          </Button>
          <Button size="sm">Download CV</Button>
        </div>
      }
    >
      {/* Hero with real workspace photo */}
      <ScrollReveal animate="fade-up">
        <div className="relative overflow-hidden rounded-3xl border border-border h-64 md:h-72 mb-8">
          <img
            src={img.portfolio.workspace}
            alt="Workspace"
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
            decoding="async"
            fetchPriority="high"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/50 to-black/20" />
          <div className="absolute inset-0 flex items-center p-8">
            <div className="flex items-center gap-6 w-full max-w-5xl mx-auto">
              <img
                src={img.portfolio.avatar}
                alt={profile.name}
                className="h-28 w-28 rounded-3xl object-cover border-4 border-primary/50 shadow-glow-sm shrink-0 hidden md:block"
                loading="lazy"
                decoding="async"
              />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <Badge variant="success" className="flex items-center gap-1.5">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                    </span>
                    Available for work
                  </Badge>
                  <Badge variant="outline" className="hidden sm:inline-flex">
                    <Code2 className="h-3 w-3" />
                    Full-Stack Developer
                  </Badge>
                </div>
                <h2 className="font-display text-3xl md:text-4xl font-bold text-white">{profile.name}</h2>
                <p className="text-primary font-medium mt-1 text-lg">{profile.title}</p>
                <p className="text-white/70 text-sm mt-3 max-w-lg">{profile.bio}</p>
                <div className="flex flex-wrap gap-4 mt-4">
                  <div className="flex items-center gap-2 text-sm text-white/70">
                    <MapPin className="h-4 w-4 text-primary" />
                    {profile.location}
                  </div>
                  <a
                    href={`mailto:${profile.email}`}
                    className="flex items-center gap-2 text-sm text-white/70 hover:text-primary transition-colors"
                  >
                    <Mail className="h-4 w-4" />
                    {profile.email}
                  </a>
                </div>
                <div className="flex flex-wrap gap-3 mt-4">
                  {socialLinks.map((social) => (
                    <a
                      key={social.label}
                      href={social.href}
                      target="_blank"
                      rel="noreferrer"
                      className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 backdrop-blur border border-white/20 text-white/70 hover:bg-white/20 hover:text-white hover:border-white/30 transition-all duration-200"
                      aria-label={social.label}
                    >
                      <social.icon className="h-5 w-5" />
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Stats Overview */}
      <ScrollReveal animate="fade-up" delay={0.1}>
        <StaggerContainer stagger={0.1}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatsCard title="Years Experience" value="5+" change={20} trend="up" changeLabel="growth" icon={Code2} iconColor="primary" />
            <StatsCard title="Projects Delivered" value="50+" change={15} trend="up" changeLabel="this year" icon={Briefcase} iconColor="emerald" />
            <StatsCard title="Happy Clients" value="30+" change={10} trend="up" changeLabel="repeat rate" icon={Star} iconColor="amber" />
            <StatsCard title="Technologies" value="20+" change={5} trend="up" changeLabel="learning" icon={Star} iconColor="violet" />
          </div>
        </StaggerContainer>
      </ScrollReveal>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Skills */}
        <ScrollReveal animate="fade-up" delay={0.2}>
          <Card animate="none" className="lg:col-span-1 h-full">
            <h3 className="font-display font-bold mb-6 flex items-center gap-2">
              <Code2 className="h-5 w-5 text-primary" />
              Technical Skills
            </h3>
            <div className="space-y-4">
              {skills.map((skill, i) => (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="font-medium">{skill.name}</span>
                    <span className="text-primary font-bold">{skill.level}%</span>
                  </div>
                  <Progress value={skill.level} className="h-2" />
                </div>
              ))}
            </div>
          </Card>
        </ScrollReveal>

        {/* Experience */}
        <ScrollReveal animate="fade-up" delay={0.25}>
          <Card animate="none" className="lg:col-span-2 h-full">
            <h3 className="font-display font-bold mb-6 flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-primary" />
              Experience
            </h3>
            <div className="space-y-5">
              {experience.map((exp, i) => (
                <div
                  key={i}
                  className="flex gap-4 pb-5 border-b border-border last:border-0 last:pb-0 relative"
                >
                  <div className="relative flex-shrink-0">
                    <div className="mt-1.5 h-3 w-3 rounded-full bg-primary border-4 border-background z-10" />
                    {i < experience.length - 1 && (
                      <div className="absolute left-1.5 top-4.5 bottom-0 w-0.5 bg-border" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between flex-wrap gap-1 mb-1">
                      <h4 className="font-semibold text-sm">{exp.role}</h4>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">{exp.period}</span>
                    </div>
                    <p className="text-sm text-primary font-medium">{exp.company}</p>
                    <p className="text-sm text-muted-foreground mt-1">{exp.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </ScrollReveal>
      </div>

      {/* Projects */}
      <ScrollReveal animate="fade-up" delay={0.3}>
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-display font-bold flex items-center gap-2">
              <Code2 className="h-5 w-5 text-primary" />
              Featured Projects
            </h3>
            <div className="flex gap-2">
              {filters.map((f) => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={cn(
                    'px-4 py-2 rounded-full text-sm font-medium transition-all',
                    activeFilter === f
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'bg-card border border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <StaggerContainer stagger={0.08}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {filteredProjects.map((proj, i) => (
                <ScrollReveal key={proj.id} animate="none">
                  <Card
                    animate="none"
                    className={cn(
                      'hover-lift group cursor-pointer h-full',
                      proj.featured && 'border-primary/30'
                    )}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="font-display font-bold text-sm group-hover:text-primary transition-colors">
                        {proj.title}
                        {proj.featured && (
                          <Badge variant="info" size="sm" className="ml-2">Featured</Badge>
                        )}
                      </h4>
                      <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                    </div>
                    <p className="text-xs text-muted-foreground mb-4 line-clamp-2">{proj.desc}</p>
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {proj.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" size="sm">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <div className="pt-4 border-t border-border flex items-center justify-between">
                      <a
                        href={proj.link}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm font-medium text-primary hover:underline flex items-center gap-1"
                      >
                        View Project
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                      <span className="text-xs text-muted-foreground">Updated 2024</span>
                    </div>
                  </Card>
                </ScrollReveal>
              ))}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>

      {/* Testimonials */}
      <ScrollReveal animate="fade-up" delay={0.4}>
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-display font-bold flex items-center gap-2">
              <Star className="h-5 w-5 text-primary" />
              Testimonials
            </h3>
            <AvatarGroup avatars={avatarGroupData} maxVisible={4} size="sm" />
          </div>
          <StaggerContainer stagger={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {testimonials.map((t, i) => (
                <ScrollReveal key={i} animate="none">
                  <Card animate="none" className="hover-lift">
                    <div className="flex gap-0.5 mb-4">
                      {Array.from({ length: 5 }).map((_, j) => (
                        <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground italic mb-5">"{t.text}"</p>
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

      {/* CTA */}
      <ScrollReveal animate="fade-up" delay={0.5}>
        <Card variant="gradient" className="p-8 text-center">
          <h3 className="font-display text-2xl font-bold mb-3">Let's Build Something Amazing</h3>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            I'm currently accepting new projects. Whether it's a full-stack application, AI integration, or a design system — let's talk.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <GlassButton variant="primary" size="lg" rightIcon={Link2} className="shadow-glow hover:shadow-glow-lg">
              Start a Project
            </GlassButton>
            <GlassButton variant="outline" size="lg" leftIcon={Mail}>
              Say Hello
            </GlassButton>
          </div>
        </Card>
      </ScrollReveal>
    </TemplateShell>
  );
}