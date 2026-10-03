import { useState } from 'react';
import { Star, Clock, Users, BookOpen, Play, Award, Search } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { courses, categories, stats, features } from './data/mockData';

const COURSE_IMGS = [
  img.education.course1,
  img.education.course2,
  img.education.course3,
  img.education.course4,
  img.education.course5,
  img.education.course6,
];
const levelColor = {
  Beginner: 'text-emerald-400',
  Intermediate: 'text-amber-400',
  Advanced: 'text-red-400',
};

export default function CourseCatalog() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [search, setSearch] = useState('');

  const filtered = courses.filter((c) => {
    const matchCat = activeCategory === 'All' || c.category === activeCategory;
    const matchSearch =
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.instructor.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <TemplateShell
      title="Course Catalog (LMS)"
      description="Browse, filter, and enroll in expert-led online courses."
      category="Education"
      actions={
        <Button size="sm">
          <BookOpen className="h-4 w-4 mr-1" />
          My Courses
        </Button>
      }
    >
      {/* Hero with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-56 mb-6">
        <img
          src={img.education.hero}
          alt="Education"
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchPriority="high"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-8 text-center">
          <Badge variant="primary" className="mb-2">
            🎓 340+ Courses · Expert Instructors
          </Badge>
          <h2 className="font-display text-3xl font-bold text-white">Invest in Your Future</h2>
          <p className="mt-1 text-white/80 text-sm">
            Programming · AI · Design · Marketing · DevOps
          </p>
          <div className="relative max-w-sm w-full mt-4 px-4">
            <Search className="absolute left-7 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search courses..."
              className="w-full rounded-xl border border-border bg-background/90 pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
            />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {stats.map((s, i) => (
          <Card
            key={i}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center hover-lift"
          >
            <p className="font-display text-2xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
              'px-3 py-1 rounded-full text-sm font-medium transition-all',
              activeCategory === cat
                ? 'bg-violet-500/20 text-violet-400 border border-violet-500/40'
                : 'bg-card border border-border text-muted-foreground hover:border-violet-500/30'
            )}
          >
            {cat}
          </button>
        ))}
        <span className="ml-auto text-sm text-muted-foreground self-center">
          {filtered.length} courses
        </span>
      </div>

      {/* Courses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((course, i) => (
          <Card
            key={course.id}
            animate="fade-up"
            animationDelay={i * 70}
            className="hover-lift group cursor-pointer"
            padding="none"
          >
            <div className="relative h-40 overflow-hidden rounded-t-lg">
              <img
                src={COURSE_IMGS[i % COURSE_IMGS.length]}
                alt={course.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
                <div className="h-12 w-12 rounded-full bg-white/90 flex items-center justify-center">
                  <Play className="h-5 w-5 text-violet-600 ml-0.5" />
                </div>
              </div>
              {course.badge && (
                <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-violet-500/90 backdrop-blur text-white text-xs font-bold">
                  {course.badge}
                </span>
              )}
              <span
                className={cn(
                  'absolute top-2 right-2 text-xs font-bold drop-shadow',
                  levelColor[course.level]
                )}
              >
                {course.level}
              </span>
            </div>
            <div className="p-4">
              <h3 className="font-display font-bold text-sm mb-1 group-hover:text-primary transition-colors line-clamp-2">
                {course.title}
              </h3>
              <p className="text-xs text-muted-foreground mb-2">{course.instructor}</p>
              <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                <span className="flex items-center gap-1">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  {course.rating}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  {course.students.toLocaleString()}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {course.duration}
                </span>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <span className="font-display font-bold text-primary">{course.price}</span>
                <Button size="sm" className="h-7 text-xs px-3">
                  Enroll
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
