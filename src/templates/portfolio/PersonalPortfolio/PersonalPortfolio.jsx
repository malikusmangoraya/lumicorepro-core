import { useState } from 'react';
import { Link2, Mail, MapPin, ExternalLink, Briefcase, Code2, Star } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { profile, skills, projects, experience, testimonials } from './data/mockData';

export default function PersonalPortfolio() {
  const [activeFilter, setActiveFilter] = useState('All');
  const filters = ['All', 'Featured'];
  const filteredProjects =
    activeFilter === 'Featured' ? projects.filter((p) => p.featured) : projects;

  return (
    <TemplateShell
      title="Personal Portfolio"
      description="Skills, projects, experience, and client testimonials."
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
      <div className="relative overflow-hidden rounded-2xl border border-border h-56 mb-6">
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
          <div className="flex items-center gap-6">
            <img
              src={img.portfolio.avatar}
              alt={profile.name}
              className="h-24 w-24 rounded-3xl object-cover border-2 border-primary/50 shadow-glow-sm shrink-0 hidden sm:block"
              loading="lazy"
              decoding="async"
            />
            <div>
              <Badge variant="success" className="mb-2">
                ✅ Available for work
              </Badge>
              <h2 className="font-display text-3xl font-bold text-white">{profile.name}</h2>
              <p className="text-primary font-medium mt-1">{profile.title}</p>
              <p className="text-white/70 text-sm mt-2 max-w-lg">{profile.bio}</p>
              <div className="flex flex-wrap gap-3 mt-3">
                <span className="flex items-center gap-1.5 text-xs text-white/60">
                  <MapPin className="h-3.5 w-3.5 text-primary" />
                  {profile.location}
                </span>
                <a
                  href={`mailto:${profile.email}`}
                  className="flex items-center gap-1.5 text-xs text-white/60 hover:text-primary transition-colors"
                >
                  <Mail className="h-3.5 w-3.5" />
                  {profile.email}
                </a>
                <a
                  href="#"
                  className="flex items-center gap-1.5 text-xs text-white/60 hover:text-primary transition-colors"
                >
                  <Link2 className="h-3.5 w-3.5" />
                  GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Skills */}
        <Card animate="fade-up" className="lg:col-span-1">
          <h3 className="font-display font-bold mb-4 flex items-center gap-2">
            <Code2 className="h-4 w-4 text-primary" />
            Skills
          </h3>
          <div className="space-y-3">
            {skills.map((skill, i) => (
              <div key={i}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-medium">{skill.name}</span>
                  <span className="text-primary font-bold">{skill.level}%</span>
                </div>
                <Progress value={skill.level} className="h-1.5" />
              </div>
            ))}
          </div>
        </Card>

        {/* Experience */}
        <Card animate="fade-up" animationDelay={100} className="lg:col-span-2">
          <h3 className="font-display font-bold mb-4 flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-primary" />
            Experience
          </h3>
          <div className="space-y-4">
            {experience.map((exp, i) => (
              <div
                key={i}
                className="flex gap-4 pb-4 border-b border-border last:border-0 last:pb-0"
              >
                <div className="mt-1 h-3 w-3 rounded-full bg-primary shrink-0" />
                <div>
                  <div className="flex items-center justify-between flex-wrap gap-1">
                    <h4 className="font-semibold text-sm">{exp.role}</h4>
                    <span className="text-xs text-muted-foreground">{exp.period}</span>
                  </div>
                  <p className="text-xs text-primary">{exp.company}</p>
                  <p className="text-xs text-muted-foreground mt-1">{exp.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Projects */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display font-bold flex items-center gap-2">
            <Code2 className="h-4 w-4 text-primary" />
            Projects
          </h3>
          <div className="flex gap-2">
            {filters.map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium transition-all',
                  activeFilter === f
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card border border-border text-muted-foreground hover:border-primary/50'
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredProjects.map((proj, i) => (
            <Card
              key={proj.id}
              animate="fade-up"
              animationDelay={i * 80}
              className={cn(
                'hover-lift group cursor-pointer',
                proj.featured && 'border-primary/30'
              )}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-display font-bold text-sm group-hover:text-primary transition-colors">
                  {proj.title}
                </h4>
                <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
              </div>
              <p className="text-xs text-muted-foreground mb-3">{proj.desc}</p>
              <div className="flex flex-wrap gap-1.5">
                {proj.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Testimonials */}
      <div>
        <h3 className="font-display font-bold mb-4 flex items-center gap-2">
          <Star className="h-4 w-4 text-primary" />
          Testimonials
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {testimonials.map((t, i) => (
            <Card key={i} animate="fade-up" animationDelay={i * 80} className="hover-lift">
              <p className="text-sm text-muted-foreground italic mb-4">"{t.text}"</p>
              <div className="flex items-center gap-3">
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
      </div>
    </TemplateShell>
  );
}
