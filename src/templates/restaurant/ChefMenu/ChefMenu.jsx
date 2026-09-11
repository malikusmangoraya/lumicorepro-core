import { useState } from 'react';
import { ChefHat, Star, Flame, Award, Leaf, Utensils } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { chef, signatures } from './data/mockData';

const DISH_IMGS = [
  img.restaurant.dish1,
  img.restaurant.dish2,
  img.restaurant.dish3,
  img.restaurant.dish4,
  img.restaurant.dish5,
  img.restaurant.dish6,
];

export default function ChefMenu() {
  const [course, setCourse] = useState('All');
  const dishes = course === 'All' ? signatures : signatures.filter((s) => s.course === course);

  return (
    <TemplateShell
      title="Chef's Signature Menu"
      description="Handcrafted recipes from Chef Imran Qureshi — slow cooking, bold spice, zero shortcuts."
      category="Restaurant"
      actions={
        <Button size="sm">
          <ChefHat className="h-4 w-4 mr-1" />
          View Full Menu
        </Button>
      }
    >
      {/* Chef hero */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-56 mb-6">
        <img
          src={img.restaurant.chef}
          alt="Executive Chef"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex items-end justify-between p-8">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16 ring-2 ring-amber-400/70">
              <img
                src={img.restaurant.chef}
                alt={chef.name}
                className="h-full w-full object-cover"
              />
            </Avatar>
            <div>
              <h2 className="font-display text-2xl font-bold text-white">{chef.name}</h2>
              <p className="text-amber-300 text-sm font-medium">{chef.title}</p>
              <p className="text-white/70 text-xs mt-0.5">
                {chef.years} years · {chef.city}
              </p>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-1 bg-black/40 backdrop-blur px-3 py-2 rounded-xl">
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
            <span className="text-sm font-bold text-white">4.9</span>
            <span className="text-xs text-white/60">· 2,300+ reviews</span>
          </div>
        </div>
      </div>

      {/* Course filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        {['All', ...new Set(signatures.map((s) => s.course))].map((c) => (
          <button
            key={c}
            onClick={() => setCourse(c)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              course === c
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {dishes.map((d, i) => (
          <Card
            key={d.name}
            animate="fade-up"
            animationDelay={(i * 50) % 300}
            className="overflow-hidden group"
          >
            <div className="relative h-40">
              <img
                src={DISH_IMGS[i % DISH_IMGS.length]}
                alt={d.name}
                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <Badge className="absolute top-3 left-3">{d.tag}</Badge>
              <span className="absolute bottom-3 right-3 flex items-center gap-1 bg-black/60 backdrop-blur px-2 py-0.5 rounded-full text-xs font-bold text-amber-300">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                {d.rating}
              </span>
            </div>
            <div className="p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-display font-semibold leading-snug">{d.name}</h3>
                <span className="font-bold text-primary text-sm shrink-0">{d.price}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">{d.desc}</p>
              <div className="flex items-center gap-2 mt-3">
                <Badge variant="outline" size="sm" className="text-[10px]">
                  {d.course}
                </Badge>
                <Button size="sm" className="h-7 text-xs ml-auto">
                  Add to Order
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Chef's note */}
      <Card animate="fade-up" animationDelay={100} padding="sm" className="mt-8 border-dashed">
        <div className="flex gap-4">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/10 flex items-center justify-center shrink-0">
            <Utensils className="h-6 w-6 text-amber-400" />
          </div>
          <div>
            <p className="font-display font-bold mb-1">Chef's Note</p>
            <p className="text-sm text-muted-foreground leading-relaxed">{chef.note}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <Badge variant="success" size="sm" className="text-[10px]">
                <Flame className="h-3 w-3 mr-1" />
                100% Halal
              </Badge>
              <Badge variant="secondary" size="sm" className="text-[10px]">
                <Leaf className="h-3 w-3 mr-1" />
                Veg options
              </Badge>
              <Badge size="sm" className="text-[10px]">
                <Award className="h-3 w-3 mr-1" />
                3× Food Awards
              </Badge>
            </div>
          </div>
        </div>
      </Card>
    </TemplateShell>
  );
}
