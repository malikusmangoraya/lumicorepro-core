import { useState } from 'react';
import { Star, Clock, Flame, Leaf, ShoppingCart, MapPin, Phone, Heart, Trash2, Minus, Plus, Truck, Shield, Headphones, Award } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, StatsCard, FeatureCard, ScrollReveal, StaggerContainer, GlassButton, AvatarGroup } from '@/components/ui';
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
  const [favorites, setFavorites] = useState([]);

  const filtered = activeCategory === 'All' ? menuItems : menuItems.filter((i) => i.category === activeCategory);
  
  const addToCart = (item) =>
    setCart((prev) => {
      const e = prev.find((c) => c.id === item.id);
      return e
        ? prev.map((c) => (c.id === item.id ? { ...c, qty: c.qty + 1 } : c))
        : [...prev, { ...item, qty: 1 }];
    });

  const removeFromCart = (itemId) =>
    setCart((prev) => prev.filter((c) => c.id !== itemId));

  const updateQty = (itemId, delta) =>
    setCart((prev) =>
      prev.map((c) => (c.id === itemId ? { ...c, qty: Math.max(1, c.qty + delta) } : c))
    );

  const toggleFavorite = (item) =>
    setFavorites((prev) => {
      const exists = prev.find((f) => f.id === item.id);
      return exists ? prev.filter((f) => f.id !== item.id) : [...prev, item];
    });

  const isFavorite = (itemId) => favorites.some((f) => f.id === itemId);
  const cartCount = cart.reduce((s, i) => s + i.qty, 0);
  const cartTotal = cart.reduce((s, i) => s + parseFloat(i.price.replace('$', '')) * i.qty, 0);

  const statsData = [
    { title: 'Menu Items', value: menuItems.length, icon: Award, iconColor: 'primary' },
    { title: 'Categories', value: categories.length, icon: Star, iconColor: 'amber' },
    { title: 'Avg Rating', value: '4.8', change: 5, trend: 'up', changeLabel: 'this month', icon: Star, iconColor: 'amber' },
    { title: 'Reviews', value: reviews.length + '+', icon: Headphones, iconColor: 'violet' },
  ];

  const featuresData = [
    { icon: Truck, iconColor: 'primary', title: 'Free Delivery', description: 'On orders over $25 within 5km radius.' },
    { icon: Shield, iconColor: 'emerald', title: 'Fresh Guarantee', description: 'Ingredients sourced daily from local markets.' },
    { icon: Headphones, iconColor: 'violet', title: '24/7 Support', description: 'We\'re here to help anytime you need.' },
    { icon: Award, iconColor: 'amber', title: 'Award Winning', description: 'Best Restaurant 2023 - Food Critics Choice.' },
  ];

  return (
    <TemplateShell
      title="Restaurant & Menu"
      description="Dine-in & delivery menu with categories, ratings, cart, and favorites."
      category="Restaurant"
      actions={
        <div className="flex items-center gap-2">
          <GlassButton variant="outline" size="sm" leftIcon={Heart}>
            Favorites ({favorites.length})
          </GlassButton>
          <Button size="sm" className="relative">
            <ShoppingCart className="h-4 w-4 mr-1" />
            Cart
            {cartCount > 0 && (
              <span className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
                {cartCount}
              </span>
            )}
          </Button>
        </div>
      }
    >
      {/* Hero Banner with real image */}
      <ScrollReveal animate="fade-up">
        <div className="relative overflow-hidden rounded-3xl border border-border h-72 mb-8">
          <img
            src={img.restaurant.hero}
            alt="Restaurant interior"
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
            decoding="async"
            fetchPriority="high"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/50 to-transparent" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.1),transparent_70%)]" />
          <div className="absolute inset-0 flex flex-col justify-end p-8">
            <div className="flex flex-wrap items-center gap-3 mb-3">
              <Badge variant="warning" className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                Open Now
              </Badge>
              <Badge variant="success" className="flex items-center gap-1.5">
                <Award className="h-3 w-3" />
                Est. 2012
              </Badge>
              <Badge variant="info" className="flex items-center gap-1.5">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                4.8 (2,400+)
              </Badge>
            </div>
            <h2 className="font-display text-3xl md:text-4xl font-bold text-white mb-2">Spice Garden Restaurant</h2>
            <p className="mt-1 text-white/80 text-base max-w-md">
              Authentic South Asian cuisine crafted with love. Dine-in, takeaway & home delivery.
            </p>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-white/70">
              <span className="flex items-center gap-1.5">
                <MapPin className="h-4 w-4 text-amber-400" /> DHA Phase 5, Karachi
              </span>
              <span className="flex items-center gap-1.5">
                <Phone className="h-4 w-4 text-amber-400" /> +92 300 1234567
              </span>
            </div>
          </div>
          <div className="absolute top-4 right-4 flex gap-2">
            <Button size="sm" className="bg-white text-foreground hover:bg-white/90">
              Reserve Table
            </Button>
            <GlassButton variant="primary" size="sm" leftIcon={Truck}>
              Order Online
            </GlassButton>
          </div>
        </div>
      </ScrollReveal>

      {/* Stats */}
      <ScrollReveal animate="fade-up" delay={0.1}>
        <StaggerContainer stagger={0.1}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {statsData.map((stat, i) => (
              <ScrollReveal key={stat.title} animate="none">
                <StatsCard
                  title={stat.title}
                  value={stat.value}
                  change={stat.change}
                  changeLabel={stat.changeLabel}
                  trend={stat.trend}
                  icon={stat.icon}
                  iconColor={stat.iconColor}
                  variant="glass"
                />
              </ScrollReveal>
            ))}
          </div>
        </StaggerContainer>
      </ScrollReveal>

      {/* Features */}
      <ScrollReveal animate="fade-up" delay={0.2}>
        <StaggerContainer stagger={0.1}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {featuresData.map((feature, i) => (
              <ScrollReveal key={feature.title} animate="none">
                <FeatureCard {...feature} variant="glass" />
              </ScrollReveal>
            ))}
          </div>
        </StaggerContainer>
      </ScrollReveal>

      {/* Category Filter */}
      <ScrollReveal animate="fade-up" delay={0.3}>
        <div className="flex flex-wrap gap-2 mb-6">
          {['All', ...categories].map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={cn(
                'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                activeCategory === cat
                  ? 'bg-primary text-primary-foreground shadow-glow-sm'
                  : 'bg-card border border-border text-muted-foreground hover:text-foreground hover:border-primary/50'
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </ScrollReveal>

      {/* Menu Grid */}
      <ScrollReveal animate="fade-up" delay={0.4}>
        <StaggerContainer stagger={0.05}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
            {filtered.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <Leaf className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                <h3 className="font-display text-lg font-bold mb-2">No items in this category</h3>
                <p className="text-muted-foreground">Try selecting a different category</p>
              </div>
            ) : (
              filtered.map((item, i) => (
                <ScrollReveal key={item.id} animate="none">
                  <Card
                    animate="none"
                    className="hover-lift group h-full flex flex-col"
                    padding="none"
                  >
                    <div className="relative h-44 overflow-hidden rounded-t-lg">
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
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(item);
                        }}
                        className="absolute bottom-2 right-2 p-2 rounded-full bg-background/90 backdrop-blur transition-all duration-200 hover:bg-primary hover:text-primary-foreground"
                        aria-label={isFavorite(item.id) ? 'Remove from favorites' : 'Add to favorites'}
                      >
                        <Heart
                          className={cn('h-4 w-4', isFavorite(item.id) ? 'fill-current text-red-500' : 'text-white/80')}
                        />
                      </button>
                    </div>
                    <div className="p-4 flex flex-col flex-1">
                      <h3 className="font-display font-semibold text-sm leading-tight mb-1">{item.name}</h3>
                      <p className="text-xs text-muted-foreground mb-2 line-clamp-2 flex-1">{item.desc}</p>
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
                      <div className="flex items-center justify-between pt-3 border-t border-border">
                        <span className="font-bold text-primary">{item.price}</span>
                        <div className="flex gap-1.5">
                          <GlassButton
                            variant="outline"
                            size="xs"
                            icon={Heart}
                            className={cn('h-7 w-7 p-0', isFavorite(item.id) && 'bg-red-500/10 text-red-500')}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleFavorite(item);
                            }}
                            aria-label={isFavorite(item.id) ? 'Remove from favorites' : 'Add to favorites'}
                          />
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
                    </div>
                  </Card>
                </ScrollReveal>
              ))
            )}
          </div>
        </StaggerContainer>
      </ScrollReveal>

      {/* Cart Sidebar Preview */}
      {cart.length > 0 && (
        <ScrollReveal animate="slide-up" delay={0.5}>
          <Card className="mb-8 border-primary/30 bg-primary/5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-bold flex items-center gap-2">
                <ShoppingCart className="h-5 w-5 text-primary" />
                Your Order ({cartCount} items)
              </h3>
              <span className="font-display text-lg font-bold text-primary">${cartTotal.toFixed(2)}</span>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {cart.map((item) => (
                <div key={item.id} className="flex items-center gap-3 p-2 rounded-lg bg-background/50">
                  <img
                    src={DISH_IMGS[item.category] || img.restaurant.dish2}
                    alt={item.name}
                    className="h-12 w-12 rounded-lg object-cover"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{item.name}</p>
                    <p className="text-xs text-muted-foreground">{item.price} each</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Button variant="ghost" size="xs" icon={Minus} onClick={() => updateQty(item.id, -1)} aria-label="Decrease quantity" />
                    <span className="font-medium w-8 text-center">{item.qty}</span>
                    <Button variant="ghost" size="xs" icon={Plus} onClick={() => updateQty(item.id, 1)} aria-label="Increase quantity" />
                    <Button variant="ghost" size="xs" icon={Trash2} onClick={() => removeFromCart(item.id)} aria-label="Remove from cart" className="text-destructive hover:text-destructive" />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex gap-2">
              <GlassButton variant="outline" size="sm" fullWidth leftIcon={Truck}>
                Checkout - ${cartTotal.toFixed(2)}
              </GlassButton>
              <Button variant="ghost" size="sm" onClick={() => setCart([])}>
                Clear Cart
              </Button>
            </div>
          </Card>
        </ScrollReveal>
      )}

      {/* Reviews */}
      <ScrollReveal animate="fade-up" delay={0.6}>
        <div className="mb-8">
          <h3 className="font-display text-lg font-bold mb-4 flex items-center gap-2">
            <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
            Customer Reviews
          </h3>
          <StaggerContainer stagger={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {reviews.map((r, i) => (
                <ScrollReveal key={i} animate="none">
                  <Card animate="none" className="hover-lift">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary text-sm">
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
                </ScrollReveal>
              ))}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>
    </TemplateShell>
  );
}