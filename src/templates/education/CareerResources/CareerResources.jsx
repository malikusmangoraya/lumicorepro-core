import { Briefcase, MapPin, Banknote, BookOpen, FileText, Quote, ArrowRight } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { img } from '@/utils/images';
import { jobs, guides, stories } from './data/mockData';

const TYPE_TONE = { 'Full-time': 'success', Internship: 'info' };

export default function CareerResources() {
  return (
    <TemplateShell
      title="Career Center"
      description="Fresh graduate? Here are jobs, guides, and playbooks from people who made it."
      category="Education"
      actions={
        <Button size="sm">
          <Briefcase className="h-4 w-4 mr-1" />
          Submit Your CV
        </Button>
      }
    >
      {/* Jobs */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-lg font-bold">Open Roles</h3>
        <Badge variant="secondary">{jobs.length} new this week</Badge>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        {jobs.map((j, i) => (
          <Card key={j.title} animate="fade-up" animationDelay={i * 70} className="hover-lift">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="min-w-0">
                <h4 className="font-display font-semibold leading-snug">{j.title}</h4>
                <p className="text-xs text-muted-foreground mt-0.5">{j.company}</p>
              </div>
              <Badge variant={TYPE_TONE[j.type]} className="text-[10px] shrink-0">
                {j.type}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground mb-3">
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {j.location}
              </span>
              <span className="flex items-center gap-1">
                <Banknote className="h-3 w-3" />
                {j.salary}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {j.tags.map((t) => (
                <Badge key={t} variant="outline" size="sm" className="text-[10px]">
                  {t}
                </Badge>
              ))}
            </div>
            <Button size="sm" className="w-full h-8 text-xs">
              Apply Now
            </Button>
          </Card>
        ))}
      </div>

      {/* Guides */}
      <h3 className="font-display text-lg font-bold mb-3">Career Playbooks</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {guides.map((g, i) => (
          <Card
            key={g.title}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="hover-lift"
          >
            <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3">
              <FileText className="h-4 w-4 text-primary" />
            </div>
            <p className="text-sm font-semibold leading-snug mb-1">{g.title}</p>
            <p className="text-xs text-muted-foreground mb-3">
              {g.type} · {g.mins}
            </p>
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
              Open <ArrowRight className="h-3 w-3" />
            </span>
          </Card>
        ))}
      </div>

      {/* Success stories */}
      <h3 className="font-display text-lg font-bold mb-3">Recent Grads, Real Offers</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {stories.map((s, i) => (
          <Card key={s.name} animate="fade-up" animationDelay={i * 80} padding="sm">
            <div className="flex gap-4">
              <Avatar className="h-12 w-12 shrink-0">
                <img
                  src={i === 0 ? img.portfolio.avatar : img.education.student}
                  alt={s.name}
                  className="h-full w-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
              </Avatar>
              <div>
                <Quote className="h-4 w-4 text-primary mb-1" />
                <p className="text-sm text-muted-foreground leading-relaxed">{s.note}</p>
                <p className="text-sm font-semibold mt-2">{s.name}</p>
                <p className="text-xs text-muted-foreground">{s.role}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card padding="sm" animate="fade-up" className="mt-6 flex flex-wrap items-center gap-3">
        <BookOpen className="h-5 w-5 text-primary shrink-0" />
        <p className="text-sm text-muted-foreground flex-1 min-w-[200px]">
          <span className="font-semibold text-foreground">Alumni job board refreshed daily.</span>{' '}
          Referrals get answered within 48 hours.
        </p>
        <Button size="sm" variant="outline" className="h-8 text-xs">
          Create Job Alert
        </Button>
      </Card>
    </TemplateShell>
  );
}
