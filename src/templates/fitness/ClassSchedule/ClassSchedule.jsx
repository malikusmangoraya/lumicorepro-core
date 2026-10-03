import { useState } from 'react';
import { Dumbbell, Users, TrendingUp, CalendarDays, Clock } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { days, classes, perks } from './data/mockData';

const CLASS_IMGS = { class1: img.fitness.class1, class2: img.fitness.class2 };

export default function ClassSchedule() {
  const [day, setDay] = useState('Mon');

  return (
    <TemplateShell
      title="Weekly Class Schedule"
      description="Book your seat in live classes — spots go fast in peak hours."
      category="Fitness"
      actions={
        <Button size="sm">
          <Dumbbell className="h-4 w-4 mr-1" />
          Download Timetable
        </Button>
      }
    >
      {/* Day tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {days.map((d) => (
          <button
            key={d}
            onClick={() => setDay(d)}
            className={cn(
              'px-5 py-2.5 rounded-xl text-sm font-bold transition-all border',
              day === d
                ? 'bg-primary text-primary-foreground border-primary shadow-glow-sm'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {d}
          </button>
        ))}
      </div>

      {/* Class cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
        {classes.map((c, i) => {
          const full = c.spots === 0;
          const pct = Math.round(((c.cap - c.spots) / c.cap) * 100);
          return (
            <Card
              key={c.time}
              animate="fade-up"
              animationDelay={(i * 60) % 300}
              className="overflow-hidden flex flex-col"
            >
              <div className="relative h-36">
                <img src={CLASS_IMGS[c.img]} alt={c.name} className="h-full w-full object-cover" loading="lazy" decoding="async" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                <span className="absolute top-3 left-3 flex items-center gap-1 bg-black/60 backdrop-blur px-2 py-0.5 rounded-full text-xs font-bold text-white">
                  <Clock className="h-3 w-3" />
                  {c.time}
                </span>
                <Badge
                  variant={full ? 'secondary' : 'success'}
                  className="absolute top-3 right-3 text-[10px]"
                >
                  {full ? 'FULL' : 'Open'}
                </Badge>
              </div>
              <div className="p-4 flex-1 flex flex-col">
                <h3 className="font-display font-semibold">{c.name}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {c.coach} · {c.level}
                </p>
                <div className="mt-3 mb-1 flex justify-between text-[11px]">
                  <span className="text-muted-foreground">
                    {c.spots} spots left of {c.cap}
                  </span>
                  <span className="font-bold text-primary">{pct}%</span>
                </div>
                <Progress value={pct} className="h-1.5" />
                <Button size="sm" className="mt-4 w-full" disabled={full}>
                  Book Class
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Perks strip */}
      <Card
        animate="fade-up"
        padding="sm"
        className="flex flex-wrap gap-4 items-center justify-between"
      >
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 flex-1">
          {perks.map((p) => (
            <span key={p} className="flex items-center gap-2 text-xs font-medium">
              <Users className="h-4 w-4 text-primary shrink-0" />
              {p}
            </span>
          ))}
        </div>
        <Button size="sm" variant="outline">
          <CalendarDays className="h-4 w-4 mr-1" />
          Add to Calendar
        </Button>
      </Card>
    </TemplateShell>
  );
}
