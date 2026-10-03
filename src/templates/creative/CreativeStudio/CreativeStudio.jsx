import { useState } from 'react';
import { Palette, Layout, Code2, Film, Users, Award, ArrowRight } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { projects, categories, services, team, stats } from './data/mockData';

const serviceIcons = { palette: Palette, layout: Layout, 'code-2': Code2, film: Film };
const catColor = {
  'UI/UX': 'bg-violet-500/15 text-violet-400',
  Branding: 'bg-pink-500/15 text-pink-400',
  '3D / Motion': 'bg-cyan-500/15 text-cyan-400',
  'Web Dev': 'bg-emerald-500/15 text-emerald-400',
};
const PROJ_IMGS = [
  img.creative.project1,
  img.creative.project2,
  img.creative.project3,
  img.creative.project4,
  img.creative.project5,
  img.creative.project6,
];
const TEAM_IMGS = [img.creative.team1, img.creative.team2, img.creative.team3, img.creative.team4];

export default function CreativeStudio() {
  const [activeCategory, setActiveCategory] = useState('All');
  const filtered =
    activeCategory === 'All' ? projects : projects.filter((p) => p.category === activeCategory);

  return (
    <TemplateShell
      title="Creative Studio"
      description="Portfolio, services, team, and brand showcase."
      category="Creative"
      actions={
        <Button size="sm">
          <ArrowRight className="h-4 w-4 mr-1" />
          Start a Project
        </Button>
      }
    >
      {/* Hero with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-64 mb-6">
        <img
          src={img.creative.hero}
          alt="Creative Studio"
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchPriority="high"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-8 text-center">
          <Badge variant="secondary" className="mb-2">
            🎨 Award-Winning Studio · Since 2018
          </Badge>
          <h2 className="font-display text-4xl font-bold text-white">
            We Create{' '}
            <span className="bg-gradient-to-r from-pink-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
              Digital Magic
            </span>
          </h2>
          <p className="mt-2 text-white/75 text-sm max-w-xl">
            Brand identities, UI/UX, web development & motion design that makes your brand
            unforgettable.
          </p>
          <div className="mt-5 flex gap-3">
            <Button size="sm" className="bg-white text-foreground hover:bg-white/90">
              View Our Work
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="border-white/40 text-white hover:bg-white/10"
            >
              Get a Quote
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {stats.map((s, i) => (
          <Card
            key={i}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center hover-lift"
          >
            <p className="font-display text-2xl font-bold bg-gradient-to-r from-pink-400 to-violet-400 bg-clip-text text-transparent">
              {s.value}
            </p>
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Services */}
      <div className="mb-8">
        <h3 className="font-display text-lg font-bold mb-4">What We Do</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {services.map((svc, i) => {
            const Icon = serviceIcons[svc.icon] || Palette;
            return (
              <Card
                key={i}
                animate="fade-up"
                animationDelay={i * 70}
                className="hover-lift cursor-pointer group"
              >
                <div className="mb-3 h-12 w-12 rounded-xl bg-gradient-to-br from-pink-500/15 to-violet-500/15 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Icon className="h-6 w-6 text-violet-400" />
                </div>
                <h3 className="font-semibold text-sm">{svc.title}</h3>
                <p className="text-xs text-muted-foreground mt-1">{svc.desc}</p>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Portfolio */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-lg font-bold">Our Work</h3>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium transition-all',
                  activeCategory === cat
                    ? 'bg-violet-500/20 text-violet-400 border border-violet-500/40'
                    : 'bg-card border border-border text-muted-foreground hover:border-violet-500/30'
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((proj, i) => (
            <Card
              key={proj.id}
              animate="fade-up"
              animationDelay={i * 70}
              className="hover-lift group cursor-pointer"
              padding="none"
            >
              <div className="relative h-48 overflow-hidden rounded-t-lg">
                <img
                  src={PROJ_IMGS[i % PROJ_IMGS.length]}
                  alt={proj.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                  decoding="async"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                {proj.featured && (
                  <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-amber-500/90 backdrop-blur text-white text-xs font-bold flex items-center gap-1">
                    <Award className="h-3 w-3" />
                    Featured
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-display font-bold text-sm group-hover:text-primary transition-colors">
                    {proj.title}
                  </h4>
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded-full text-xs font-medium shrink-0',
                      catColor[proj.category] || 'bg-primary/10 text-primary'
                    )}
                  >
                    {proj.category}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{proj.client}</span>
                  <span>{proj.year}</span>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {proj.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 rounded-full bg-card border border-border text-xs text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Team with real photos */}
      <div>
        <h3 className="font-display text-lg font-bold mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          The Team
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {team.map((member, i) => (
            <Card
              key={i}
              animate="fade-up"
              animationDelay={i * 70}
              className="hover-lift text-center"
              padding="sm"
            >
              <img
                src={TEAM_IMGS[i % TEAM_IMGS.length]}
                alt={member.name}
                className="mx-auto mb-3 h-16 w-16 rounded-2xl object-cover ring-2 ring-border"
                loading="lazy"
                decoding="async"
              />
              <h4 className="font-semibold text-sm">{member.name}</h4>
              <p className="text-xs text-primary mt-0.5">{member.role}</p>
              <p className="text-xs text-muted-foreground mt-1">{member.exp} experience</p>
            </Card>
          ))}
        </div>
      </div>
    </TemplateShell>
  );
}
