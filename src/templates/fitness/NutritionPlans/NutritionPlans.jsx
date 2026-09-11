import { Beef, Timer, Utensils, Apple, Droplets } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { img } from '@/utils/images';
import { goal, meals, rules } from './data/mockData';

const MEAL_IMGS = [img.fitness.class1, img.fitness.class2];
const MACROS = [
  { label: 'Protein', cur: goal.protein, target: goal.protein, color: 'bg-primary' },
  { label: 'Carbs', cur: 176, target: goal.carbs, color: 'bg-amber-400' },
  { label: 'Fat', cur: 42, target: goal.fat, color: 'bg-rose-400' },
];

export default function NutritionPlans() {
  return (
    <TemplateShell
      title="Personalized Nutrition Plan"
      description="A 60-day, pakistani-food-friendly plan built around your macros."
      category="Fitness"
      actions={
        <Button size="sm">
          <Apple className="h-4 w-4 mr-1" />
          Edit My Plan
        </Button>
      }
    >
      {/* Goal header */}
      <Card animate="fade-up" className="relative overflow-hidden mb-6">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500/15 via-primary/5 to-transparent" />
        <div className="relative flex items-center gap-4 flex-wrap">
          <div className="h-14 w-14 rounded-2xl bg-primary/15 flex items-center justify-center shrink-0">
            <Utensils className="h-7 w-7 text-primary" />
          </div>
          <div className="flex-1 min-w-[180px]">
            <h3 className="font-display text-lg font-bold">Your {goal.plan} Plan</h3>
            <p className="text-xs text-muted-foreground">
              Day 12 of {goal.days} · {goal.cal} kcal daily target
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            {MACROS.map((m) => (
              <div key={m.label} className="min-w-[130px]">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">{m.label}</span>
                  <span className="font-bold">
                    {m.cur}g<span className="text-muted-foreground font-medium">/{m.target}g</span>
                  </span>
                </div>
                <Progress
                  value={Math.min(100, (m.cur / m.target) * 100)}
                  className={`h-1.5 ${m.color}`}
                />
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Meals */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        {meals.map((m, i) => (
          <Card key={m.type} animate="fade-up" animationDelay={i * 70} className="overflow-hidden">
            <div className="relative h-32">
              <img src={MEAL_IMGS[i % 2]} alt={m.name} className="h-full w-full object-cover" />
              <Badge className="absolute top-3 left-3 text-[10px]">{m.type}</Badge>
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <h4 className="font-display font-semibold text-sm leading-snug">{m.name}</h4>
                <span className="text-primary font-bold text-sm">{m.cal}</span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1 flex items-center gap-1">
                <Timer className="h-3 w-3" />
                Prep {m.ready} · {m.time}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                P{m.protein} · C{Math.round(m.cal * 0.5) / 5} · F{Math.round(m.cal * 0.08)}
              </p>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rules */}
        <Card animate="fade-up" animationDelay={80} padding="sm">
          <h4 className="font-display font-bold mb-3 flex items-center gap-2">
            <Beef className="h-4 w-4 text-primary" />
            Daily Non-Negotiables
          </h4>
          <ul className="space-y-2.5">
            {rules.map((r, i) => (
              <li key={r} className="flex items-center gap-3 text-sm">
                <Badge
                  variant="outline"
                  size="sm"
                  className="h-6 w-6 rounded-full justify-center text-[10px]"
                >
                  {i + 1}
                </Badge>
                {r}
              </li>
            ))}
          </ul>
        </Card>

        {/* Hydration + swap */}
        <Card animate="fade-up" animationDelay={140} padding="sm" className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h4 className="font-display font-bold flex items-center gap-2">
              <Droplets className="h-4 w-4 text-sky-400" />
              Hydration Today
            </h4>
            <span className="text-xs text-muted-foreground">1.4 / 3.0 L</span>
          </div>
          <Progress value={47} className="h-2 mb-5" />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              'Swap: Biryani → Daal Chawal (save 220 kcal)',
              'Swap: Chai snack → Nuts & coffee',
              'Post-workout: whey + milk within 30 min',
            ].map((s) => (
              <div key={s} className="rounded-xl bg-muted/60 p-3 text-xs leading-relaxed">
                <span className="font-bold text-primary">Pro tip: </span>
                {s}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </TemplateShell>
  );
}
