import { useState } from 'react';
import { Dumbbell, Flame, Users, Calendar, Check, Clock, Zap } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { plans, classes, trainers, stats } from './data/mockData';

const TRAINER_IMGS = [
  img.fitness.trainer1,
  img.fitness.trainer2,
  img.fitness.trainer3,
  img.fitness.trainer4,
];
const intensityColor = { High: 'text-red-400', Medium: 'text-amber-400', Low: 'text-emerald-400' };

export default function GymLanding() {
  const [activeDay, setActiveDay] = useState('Today');
  const days = ['Today', 'Tomorrow', 'Wed', 'Thu', 'Fri'];

  return (
    <TemplateShell
      title="Gym & Fitness"
      description="Membership plans, class schedule, and trainer profiles."
      category="Fitness"
      actions={
        <Button size="sm">
          <Zap className="h-4 w-4 mr-1" />
          Join Now
        </Button>
      }
    >
      {/* Hero with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-64 mb-6">
        <img
          src={img.fitness.hero}
          alt="Gym"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-center p-8">
          <Badge variant="danger" className="mb-3 w-fit">
            💪 3,200+ Active Members
          </Badge>
          <h2 className="font-display text-4xl font-bold text-white leading-tight">
            Push Your
            <br />
            Limits Daily
          </h2>
          <p className="mt-2 text-white/75 text-sm max-w-xs">
            35+ expert trainers · 84 weekly classes · Personalized nutrition plans.
          </p>
          <div className="mt-5 flex gap-3">
            <Button size="sm" className="bg-white text-foreground hover:bg-white/90">
              <Flame className="h-4 w-4 mr-1 text-red-500" />
              Start Free Trial
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="border-white/40 text-white hover:bg-white/10"
            >
              View Plans
            </Button>
          </div>
        </div>
        <img
          src={img.fitness.gym1}
          alt="Gym interior"
          className="absolute right-0 top-0 h-full w-1/2 object-cover opacity-40"
        />
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
            <p className="font-display text-2xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Class Schedule */}
      <div className="mb-8">
        <h3 className="font-display text-lg font-bold mb-4">Class Schedule</h3>
        <div className="flex gap-2 mb-4">
          {days.map((d) => (
            <button
              key={d}
              onClick={() => setActiveDay(d)}
              className={cn(
                'px-3 py-1 rounded-full text-sm font-medium transition-all',
                activeDay === d
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-card border border-border text-muted-foreground hover:border-primary/50'
              )}
            >
              {d}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {classes.map((cls, i) => (
            <Card key={i} animate="fade-up" animationDelay={i * 60} className="hover-lift group">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-display font-bold">{cls.name}</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">{cls.trainer}</p>
                </div>
                <span className={cn('text-xs font-bold', intensityColor[cls.intensity])}>
                  <Flame className="h-3 w-3 inline mr-0.5" />
                  {cls.intensity}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {cls.time} · {cls.duration}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" />
                  {cls.spots} spots
                </span>
              </div>
              <Progress value={(10 - cls.spots) * 10} className="h-1.5 mb-3" />
              <Button size="sm" variant="outline" className="w-full text-xs h-8">
                <Calendar className="h-3 w-3 mr-1" />
                Book Class
              </Button>
            </Card>
          ))}
        </div>
      </div>

      {/* Pricing Plans */}
      <div className="mb-8">
        <h3 className="font-display text-lg font-bold mb-4">Membership Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.map((plan, i) => (
            <Card
              key={plan.id}
              animate="fade-up"
              animationDelay={i * 80}
              className={cn(
                'hover-lift relative',
                plan.highlighted && 'border-primary shadow-glow-sm'
              )}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  Most Popular
                </div>
              )}
              <h4 className="font-display font-bold text-lg">{plan.name}</h4>
              <div className="mt-2 mb-4">
                <span className="font-display text-3xl font-bold">{plan.price}</span>
                <span className="text-sm text-muted-foreground">{plan.period}</span>
              </div>
              <ul className="space-y-2 mb-4">
                {plan.features.map((feat, j) => (
                  <li key={j} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Check className="h-4 w-4 text-primary shrink-0" />
                    {feat}
                  </li>
                ))}
              </ul>
              <Button
                size="sm"
                variant={plan.highlighted ? 'default' : 'outline'}
                className="w-full"
              >
                Choose {plan.name}
              </Button>
            </Card>
          ))}
        </div>
      </div>

      {/* Trainers with real photos */}
      <div>
        <h3 className="font-display text-lg font-bold mb-4">Expert Trainers</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {trainers.map((t, i) => (
            <Card
              key={i}
              animate="fade-up"
              animationDelay={i * 70}
              className="hover-lift text-center"
              padding="sm"
            >
              <img
                src={TRAINER_IMGS[i % TRAINER_IMGS.length]}
                alt={t.name}
                className="mx-auto mb-3 h-16 w-16 rounded-2xl object-cover ring-2 ring-border"
              />
              <h4 className="font-semibold text-sm">{t.name}</h4>
              <p className="text-xs text-primary mt-0.5">{t.specialty}</p>
              <div className="flex justify-center gap-3 mt-2 text-xs text-muted-foreground">
                <span>
                  <Dumbbell className="h-3 w-3 inline mr-0.5" />
                  {t.exp}
                </span>
                <span>
                  <Users className="h-3 w-3 inline mr-0.5" />
                  {t.clients}
                </span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </TemplateShell>
  );
}
