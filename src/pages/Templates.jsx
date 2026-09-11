import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ShoppingBag,
  Sparkles,
  Briefcase,
  Utensils,
  Home,
  HeartPulse,
  Dumbbell,
  GraduationCap,
  Plane,
  User,
  Palette,
  Search,
  ArrowRight,
  X,
  Filter,
} from 'lucide-react';
import { TEMPLATE_CATALOG } from '@/templates/catalog';
import { Card, Badge, Button, Input, IconButton } from '@/components/ui';
import { cn } from '@/utils';

/* ── category meta ──────────────────────────────────────────────── */
const CATEGORIES = [
  { label: 'All', icon: Filter, tone: 'text-muted-foreground' },
  { label: 'Dashboard', icon: LayoutDashboard, tone: 'text-blue-400' },
  { label: 'E-Commerce', icon: ShoppingBag, tone: 'text-emerald-400' },
  { label: 'AI', icon: Sparkles, tone: 'text-violet-400' },
  { label: 'Business', icon: Briefcase, tone: 'text-amber-400' },
  { label: 'Restaurant', icon: Utensils, tone: 'text-orange-400' },
  { label: 'Real Estate', icon: Home, tone: 'text-indigo-400' },
  { label: 'Healthcare', icon: HeartPulse, tone: 'text-rose-400' },
  { label: 'Fitness', icon: Dumbbell, tone: 'text-red-400' },
  { label: 'Education', icon: GraduationCap, tone: 'text-purple-400' },
  { label: 'Travel', icon: Plane, tone: 'text-sky-400' },
  { label: 'Portfolio', icon: User, tone: 'text-teal-400' },
  { label: 'Creative', icon: Palette, tone: 'text-pink-400' },
];

const catMeta = Object.fromEntries(CATEGORIES.map((c) => [c.label, c]));

/* ── gradient per category ──────────────────────────────────────── */
const CAT_GRADIENT = {
  Dashboard: 'from-blue-500/15 to-blue-900/10',
  'E-Commerce': 'from-emerald-500/15 to-emerald-900/10',
  AI: 'from-violet-500/15 to-violet-900/10',
  Business: 'from-amber-500/15 to-amber-900/10',
  Restaurant: 'from-orange-500/15 to-orange-900/10',
  'Real Estate': 'from-indigo-500/15 to-indigo-900/10',
  Healthcare: 'from-rose-500/15 to-rose-900/10',
  Fitness: 'from-red-500/15 to-red-900/10',
  Education: 'from-purple-500/15 to-purple-900/10',
  Travel: 'from-sky-500/15 to-sky-900/10',
  Portfolio: 'from-teal-500/15 to-teal-900/10',
  Creative: 'from-pink-500/15 to-pink-900/10',
};

export default function TemplatesHub() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    return TEMPLATE_CATALOG.filter((t) => {
      const matchCat = activeCategory === 'All' || t.category === activeCategory;
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        t.title.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        (t.tags || []).some((tag) => tag.includes(q));
      return matchCat && matchSearch;
    });
  }, [activeCategory, search]);

  /* grouped for the "All" view */
  const groups = useMemo(() => {
    if (activeCategory !== 'All') return null;
    const map = {};
    TEMPLATE_CATALOG.forEach((t) => {
      if (!map[t.category]) map[t.category] = [];
      map[t.category].push(t);
    });
    return map;
  }, [activeCategory]);

  const catCounts = useMemo(() => {
    const m = {};
    TEMPLATE_CATALOG.forEach((t) => {
      m[t.category] = (m[t.category] || 0) + 1;
    });
    return m;
  }, []);

  return (
    <div className="space-y-8 animate-page-enter">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="animate-fade-in-up">
        <div className="flex items-center gap-3 mb-2">
          <Badge variant="info">60 Templates</Badge>
          <Badge variant="secondary">12 Categories</Badge>
          <Badge variant="success">Market-Ready</Badge>
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
          Template Gallery
        </h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          60 production-ready templates across 12 industries — each with real mock data, dark mode,
          and responsive layout. Browse, preview, and copy into your next project.
        </p>
      </header>

      {/* ── Search Bar ─────────────────────────────────────────── */}
      <div className="relative max-w-md animate-fade-in-up" style={{ animationDelay: '60ms' }}>
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search templates, categories, or tags..."
          leftIcon={Search}
          className="w-full"
          inputClassName="rounded-xl py-2.5 pl-10 pr-10"
          aria-label="Search templates"
        />
        {search && (
          <IconButton
            icon={X}
            label="Clear search"
            size="sm"
            variant="ghost"
            onClick={() => setSearch('')}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          />
        )}
      </div>

      {/* ── Category Filter Tabs ────────────────────────────────── */}
      <div className="flex flex-wrap gap-2 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const count = cat.label === 'All' ? TEMPLATE_CATALOG.length : catCounts[cat.label] || 0;
          const active = activeCategory === cat.label;
          return (
            <Button
              key={cat.label}
              onClick={() => setActiveCategory(cat.label)}
              variant={active ? 'primary' : 'outline'}
              size="sm"
              className={cn(
                'rounded-full px-3.5 py-1.5',
                !active &&
                  'bg-card border-border text-muted-foreground hover:text-foreground hover:border-primary/40'
              )}
              aria-pressed={active}
            >
              <Icon
                className={cn('h-3.5 w-3.5', active ? 'text-primary-foreground' : cat.tone)}
                aria-hidden="true"
              />
              <span>{cat.label}</span>
              <span
                className={cn(
                  'px-1.5 py-0.5 rounded-full text-xs font-bold',
                  active ? 'bg-white/20 text-primary-foreground' : 'bg-muted text-muted-foreground'
                )}
              >
                {count}
              </span>
            </Button>
          );
        })}
      </div>

      {/* ── Results summary ─────────────────────────────────────── */}
      {search && (
        <p className="text-sm text-muted-foreground animate-fade-in">
          Found <span className="font-semibold text-foreground">{filtered.length}</span> template
          {filtered.length !== 1 ? 's' : ''} for "<span className="text-primary">{search}</span>"
        </p>
      )}

      {/* ── Grouped All View ────────────────────────────────────── */}
      {activeCategory === 'All' && !search && groups && (
        <div className="space-y-10">
          {CATEGORIES.filter((c) => c.label !== 'All').map((cat, gi) => {
            const items = groups[cat.label];
            if (!items) return null;
            const Icon = cat.icon;
            return (
              <section
                key={cat.label}
                className="animate-fade-in-up"
                style={{ animationDelay: `${gi * 40}ms` }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={cn(
                      'h-8 w-8 rounded-lg flex items-center justify-center bg-gradient-to-br',
                      CAT_GRADIENT[cat.label] || 'from-primary/15 to-primary/5'
                    )}
                  >
                    <Icon className={cn('h-4 w-4', cat.tone)} />
                  </div>
                  <h2 className="font-display text-xl font-bold">{cat.label}</h2>
                  <Badge variant="secondary" className="text-xs">
                    {items.length}
                  </Badge>
                </div>
                <TemplateGrid items={items} catGradient={CAT_GRADIENT[cat.label]} />
              </section>
            );
          })}
        </div>
      )}

      {/* ── Filtered / Search View ──────────────────────────────── */}
      {(activeCategory !== 'All' || search) && (
        <>
          {activeCategory !== 'All' && !search && (
            <div className="flex items-center gap-3 mb-2 animate-fade-in">
              {(() => {
                const meta = catMeta[activeCategory];
                const Icon = meta?.icon || Filter;
                return (
                  <>
                    <div
                      className={cn(
                        'h-8 w-8 rounded-lg flex items-center justify-center bg-gradient-to-br',
                        CAT_GRADIENT[activeCategory] || 'from-primary/15 to-primary/5'
                      )}
                    >
                      <Icon className={cn('h-4 w-4', meta?.tone || 'text-primary')} />
                    </div>
                    <h2 className="font-display text-xl font-bold">{activeCategory}</h2>
                    <Badge variant="secondary" className="text-xs">
                      {filtered.length}
                    </Badge>
                  </>
                );
              })()}
            </div>
          )}
          <TemplateGrid items={filtered} catGradient={CAT_GRADIENT[activeCategory]} />
        </>
      )}

      {/* ── No results ──────────────────────────────────────────── */}
      {filtered.length === 0 && (
        <div className="text-center py-16 animate-fade-in-up">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="font-display text-lg font-bold mb-2">No templates found</h3>
          <p className="text-muted-foreground text-sm mb-4">
            Try a different search term or category.
          </p>
          <Button
            onClick={() => {
              setSearch('');
              setActiveCategory('All');
            }}
            variant="primary"
            leftIcon={X}
          >
            Clear filters
          </Button>
        </div>
      )}
    </div>
  );
}

/* ── Template Card Grid ─────────────────────────────────────────── */
function TemplateGrid({ items, catGradient }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {items.map((t, i) => (
        <TemplateCard
          key={t.id}
          template={t}
          index={i}
          gradient={catGradient || CAT_GRADIENT[t.category]}
        />
      ))}
    </div>
  );
}

function TemplateCard({ template: t, index, gradient }) {
  const meta = catMeta[t.category];
  const Icon = meta?.icon || Filter;
  const navigate = useNavigate();

  return (
    <Card
      className="h-full flex flex-col transition-all duration-200 hover-lift hover:border-primary/40 hover:shadow-card-hover overflow-hidden cursor-pointer group"
      padding="none"
      animate="fade-up"
      animationDelay={(index * 50) % 400}
      onClick={() => navigate(t.route)}
    >
      {/* Preview thumbnail */}
      <div
        className={cn(
          'h-28 bg-gradient-to-br flex items-center justify-center relative overflow-hidden',
          gradient || 'from-primary/15 to-primary/5'
        )}
      >
        <div className="absolute inset-0 bg-gradient-mesh opacity-50" />
        <span className="text-4xl relative z-10 group-hover:scale-110 transition-transform duration-300">
          {t.icon || '📄'}
        </span>
        <div className="absolute top-2 right-2">
          <Badge
            variant="outline"
            className="bg-background/70 backdrop-blur border-border/50 text-[11px]"
          >
            <span className={cn(meta?.tone)}>{t.category}</span>
          </Badge>
        </div>
      </div>

      {/* Info */}
      <div className="flex flex-col flex-1 p-4">
        <h3 className="font-display font-semibold text-sm group-hover:text-primary transition-colors leading-snug">
          {t.title}
        </h3>
        <p className="mt-1.5 text-xs text-muted-foreground flex-1 leading-relaxed">
          {t.description}
        </p>
        {/* Tags */}
        {t.tags && (
          <div className="flex flex-wrap gap-1 mt-3">
            {t.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0.5">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/60">
          <div
            className={cn(
              'h-5 w-5 rounded flex items-center justify-center',
              gradient?.split(' ')[0].replace('from-', 'bg-') || 'bg-primary/10'
            )}
          >
            <Icon className={cn('h-3 w-3', meta?.tone || 'text-primary')} />
          </div>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
            Preview{' '}
            <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
          </span>
        </div>
      </div>
    </Card>
  );
}
