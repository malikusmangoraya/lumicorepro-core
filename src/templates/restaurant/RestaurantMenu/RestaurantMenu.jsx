import { useState } from 'react';
import { Star, Clock, Flame, Leaf, ShoppingCart, MapPin, Phone } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { categories, menuItems, reviews } from './data/mockData';

/* map category → Unsplash dish image */
const DISH_IMGS = {
  Starters: img.restaurant.dish1,
  Mains: img.restaurant.dish5,
  Grills: img.restaurant.dish3,
  Desserts: img.restaurant.dish6,
  Drinks: img.restaurant.dish4,
};

export default function RestaurantMenu() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [cart, setCart] = useState([]);

  const filtered =
    activeCategory === 'All' ? menuItems : menuItems.filter((i) => i.category === activeCategory);
  const addToCart = (item) =>
    setCart((prev) => {
      const e = prev.find((c) => c.id === item.id);
      return e
        ? prev.map((c) => (c.id === item.id ? { ...c, qty: c.qty + 1 } : c))
        : [...prev, { ...item, qty: 1 }];
    });
  const cartCount = cart.reduce((s, i) => s + i.qty, 0);

  return (
    <TemplateShell
      title="Restaurant & Menu"
      description="Dine-in & delivery menu with categories, ratings, and cart."
      category="Restaurant"
      actions={
        <Button size="sm" className="relative">
          <ShoppingCart className="h-4 w-4 mr-1" />
          Cart
          {cartCount > 0 && (
            <span className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
              {cartCount}
            </span>
          )}
        </Button>
      }
    >
      {/* Hero Banner with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-64 mb-6">
        <img
          src={img.restaurant.hero}
          alt="Restaurant"
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchPriority="high"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <Badge variant="warning" className="mb-2 w-fit">
            🍽️ Open Now · Est. 2012
          </Badge>
          <h2 className="font-display text-3xl font-bold text-white">Spice Garden Restaurant</h2>
          <p className="mt-1 text-white/80 text-sm max-w-md">
            Authentic South Asian cuisine crafted with love. Dine-in, takeaway & home delivery.
          </p>
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-white/70">
            <span className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-amber-400" /> DHA Phase 5, Karachi
            </span>
            <span className="flex items-center gap-1.5">
              <Phone className="h-3.5 w-3.5 text-amber-400" /> +92 300 1234567
            </span>
            <span className="flex items-center gap-1.5">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" /> 4.8 (2,400+ reviews)
            </span>
          </div>
        </div>
        <div className="absolute top-4 right-4 flex gap-2">
          <Button size="sm" className="bg-white text-foreground hover:bg-white/90">
            Reserve Table
          </Button>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200',
              activeCategory === cat
                ? 'bg-primary text-primary-foreground shadow-glow-sm'
                : 'bg-card border border-border text-muted-foreground hover:text-foreground hover:border-primary/50'
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Menu Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        {filtered.map((item, i) => (
          <Card
            key={item.id}
            animate="fade-up"
            animationDelay={i * 60}
            className="hover-lift group"
            padding="none"
          >
            <div className="relative h-40 overflow-hidden rounded-t-lg">
              <img
                src={DISH_IMGS[item.category] || img.restaurant.dish2}
                alt={item.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              {item.badge && (
                <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-red-500/90 backdrop-blur text-white text-xs font-bold">
                  {item.badge}
                </span>
              )}
              {item.veg ? (
                <Leaf className="absolute top-2 right-2 h-4 w-4 text-emerald-400 drop-shadow" />
              ) : (
                <Flame className="absolute top-2 right-2 h-4 w-4 text-orange-400 drop-shadow" />
              )}
            </div>
            <div className="p-4">
              <h3 className="font-display font-semibold text-sm leading-tight mb-1">{item.name}</h3>
              <p className="text-xs text-muted-foreground mb-2 line-clamp-2">{item.desc}</p>
              <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                <span className="flex items-center gap-1">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  {item.rating}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {item.time}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary text-sm">{item.price}</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => addToCart(item)}
                  className="h-7 text-xs px-2"
                >
                  + Add
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Reviews */}
      <div>
        <h3 className="font-display text-lg font-bold mb-4">Customer Reviews</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {reviews.map((r, i) => (
            <Card key={i} animate="fade-up" animationDelay={i * 80} className="hover-lift">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-9 w-9 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary text-sm">
                  {r.name.charAt(0)}
                </div>
                <div>
                  <p className="font-semibold text-sm">{r.name}</p>
                  <p className="text-xs text-muted-foreground">{r.date}</p>
                </div>
              </div>
              <div className="flex gap-0.5 mb-2">
                {Array.from({ length: r.stars }).map((_, j) => (
                  <Star key={j} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                ))}
              </div>
              <p className="text-sm text-muted-foreground">"{r.text}"</p>
            </Card>
          ))}
        </div>
      </div>
    </TemplateShell>
  );
}
