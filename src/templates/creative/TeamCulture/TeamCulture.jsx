import { Sparkles, Heart, Wrench, Gift, Quote, Check } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { img } from '@/utils/images';
import { team, values, perks } from './data/mockData';

const TEAM_IMGS = [img.creative.team1, img.creative.team2, img.creative.team3, img.creative.team4];
const VALUE_ICONS = [Sparkles, Heart, Wrench];

export default function TeamCulture() {
  return (
    <TemplateShell
      title="The Studio & The People"
      description="A small senior team that picks projects by curiosity, not capacity."
      category="Creative"
      actions={
        <Button size="sm">
          <Gift className="h-4 w-4 mr-1" />
          We're Hiring
        </Button>
      }
    >
      {/* Values */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {values.map((v, i) => {
          const Icon = VALUE_ICONS[i];
          return (
            <Card key={v.title} animate="fade-up" animationDelay={i * 70} padding="sm">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-pink-500/20 to-rose-500/10 flex items-center justify-center mb-3">
                <Icon className="h-5 w-5 text-rose-400" />
              </div>
              <p className="font-display font-semibold mb-1">{v.title}</p>
              <p className="text-xs text-muted-foreground leading-relaxed">{v.desc}</p>
            </Card>
          );
        })}
      </div>

      {/* Team */}
      <h3 className="font-display text-lg font-bold mb-4">Core Team</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {team.map((m, i) => (
          <Card
            key={m.name}
            animate="fade-up"
            animationDelay={(i * 80) % 300}
            className="overflow-hidden group"
          >
            <div className="relative h-52 overflow-hidden">
              <img
                src={TEAM_IMGS[i]}
                alt={m.name}
                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-transparent" />
              <div className="absolute bottom-3 left-3">
                <p className="font-display font-bold text-white">{m.name}</p>
                <p className="text-rose-300 text-xs">{m.role}</p>
              </div>
            </div>
            <div className="p-4">
              <Quote className="h-4 w-4 text-rose-400 mb-1.5" />
              <p className="text-xs text-muted-foreground italic leading-relaxed">{m.quote}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Perks */}
      <Card animate="fade-up" className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-pink-500/10 via-transparent to-transparent" />
        <div className="relative p-5">
          <h4 className="font-display font-bold mb-3">Why People Stay</h4>
          <div className="flex flex-wrap gap-2">
            {perks.map((p) => (
              <Badge key={p} variant="outline" size="sm" className="text-[11px] py-1 px-3">
                <Check className="h-3 w-3 text-emerald-400 mr-1" />
                {p}
              </Badge>
            ))}
          </div>
        </div>
      </Card>
    </TemplateShell>
  );
}
