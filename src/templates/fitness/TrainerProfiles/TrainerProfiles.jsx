import { Star, Medal, Users, TrendingUp, Flame } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { img } from '@/utils/images';
import { trainers, stats } from './data/mockData';

const TRAINER_IMGS = {
  trainer1: img.fitness.trainer1,
  trainer2: img.fitness.trainer2,
  trainer3: img.fitness.trainer3,
  trainer4: img.fitness.trainer4,
};

export default function TrainerProfiles() {
  return (
    <TemplateShell
      title="Meet Your Coaches"
      description="Certified trainers, proven results, zero bro-science."
      category="Fitness"
      actions={
        <Button size="sm">
          <Flame className="h-4 w-4 mr-1" />
          Book Free Intro
        </Button>
      }
    >
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {stats.map((s, i) => (
          <Card
            key={s.label}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center"
          >
            <p className="font-display text-xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {trainers.map((t, i) => (
          <Card
            key={t.name}
            animate="fade-up"
            animationDelay={(i * 80) % 300}
            className="overflow-hidden flex flex-col"
          >
            <div className="relative h-56">
              <img src={TRAINER_IMGS[t.img]} alt={t.name} className="h-full w-full object-cover" loading="lazy" decoding="async" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-transparent" />
              <Badge variant="secondary" className="absolute top-3 left-3 text-[10px]">
                {t.cert}
              </Badge>
              <span className="absolute top-3 right-3 flex items-center gap-1 bg-black/60 backdrop-blur px-2 py-0.5 rounded-full text-xs font-bold text-amber-300">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                {t.rating}
              </span>
              <div className="absolute bottom-3 left-3">
                <p className="font-display font-bold text-white">{t.name}</p>
                <p className="text-white/75 text-xs">{t.role}</p>
              </div>
            </div>
            <div className="p-4 flex-1 flex flex-col">
              <p className="text-xs italic text-muted-foreground leading-relaxed">{t.style}</p>
              <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Medal className="h-3.5 w-3.5 text-primary" />
                  {t.exp} yrs
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5 text-primary" />
                  {t.students}
                </span>
                <span className="flex items-center gap-1">
                  <TrendingUp className="h-3.5 w-3.5 text-primary" />
                  Progress track
                </span>
              </div>
              <Button size="sm" variant="outline" className="w-full mt-4">
                View Profile
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
