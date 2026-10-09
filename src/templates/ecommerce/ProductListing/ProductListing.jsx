import { useMemo, useState } from 'react';
import { Search, Star, ShoppingCart, Filter, Grid, List, Truck, Shield, RotateCcw, Headphones } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge, Input, StatsCard, FeatureCard, ScrollReveal, StaggerContainer, GlassButton } from '@/components/ui';
import { products, categories } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';
import { img } from '@/utils/images';

const PRODUCT_IMGS = [
  img.ecommerce.product1,
  img.ecommerce.product2,
  img.ecommerce.product3,
  img.ecommerce.product4,
  img.ecommerce.product5,
  img.ecommerce.product6,
  img.ecommerce.product7,
  img.ecommerce.product8,
];

const features = [
  {
    icon: Truck,
    iconColor: 'primary',
    title: 'Free Shipping',
    description: 'On orders over $50. Fast delivery within 2-3 business days.',
  },
  {
    icon: Shield,
    iconColor: 'emerald',
    title: 'Secure Payment',
    description: '100% secure checkout with SSL encryption and fraud protection.',
  },
  {
    icon: RotateCcw,
    iconColor: 'amber',
    title: 'Easy Returns',
    description: '30-day hassle-free returns. No questions asked.',
  },
  {
    icon: Headphones,
    iconColor: 'violet',
    title: '24/7 Support',
    description: 'Our team is here to help you anytime, anywhere.',
  },
];

const stats = [
  { title: 'Total Products', value: products.length, change: 12, trend: 'up', changeLabel: 'vs last month', icon: Star, iconColor: 'primary' },
  { title: 'Categories', value: categories.length, change: 0, trend: 'neutral', changeLabel: 'active', icon: Grid, iconColor: 'emerald' },
  { title: 'Avg Rating', value: '4.8', change: 5, trend: 'up', changeLabel: 'customer satisfaction', icon: Star, iconColor: 'amber' },
  { title: 'In Stock', value: products.filter(p => p.inStock).length, change: 8, trend: 'up', changeLabel: 'new arrivals', icon: Shield, iconColor: 'violet' },
];

export default function ProductListing() {
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState('all');
  const [view, setView] = useState('grid');
  const q = useDebounce(query);
  const list = useMemo(
    () =>
      products.filter(
        (p) =>
          (cat === 'all' || p.category === cat) && p.name.toLowerCase().includes(q.toLowerCase())
      ),
    [q, cat]
  );

  return (
    <TemplateShell
      title="Product Listing"
      description="Browse, filter, and sort products with enhanced UI."
      category="E-Commerce"
      actions={
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setView('grid')} aria-label="Grid view">
            <Grid className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setView('list')} aria-label="List view">
            <List className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" leftIcon={Filter}>
            Filters
          </Button>
        </div>
      }
    >
      {/* Stats Overview */}
      <ScrollReveal animate="fade-up">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {stats.map((stat, i) => (
            <ScrollReveal key={stat.title} animate="fade-up" delay={i * 0.1}>
              <StatsCard
                title={stat.title}
                value={stat.value}
                change={stat.change}
                changeLabel={stat.changeLabel}
                icon={stat.icon}
                iconColor={stat.iconColor}
                trend={stat.trend}
              />
            </ScrollReveal>
          ))}
        </div>
      </ScrollReveal>

      {/* Features */}
      <ScrollReveal animate="fade-up">
        <div className="mb-8">
          <h3 className="font-display text-lg font-bold mb-4">Why Shop With Us</h3>
          <StaggerContainer stagger={0.1}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {features.map((feature, i) => (
                <FeatureCard
                  key={feature.title}
                  {...feature}
                  variant="glass"
                  animate="none"
                />
              ))}
            </div>
          </StaggerContainer>
        </div>
      </ScrollReveal>

      {/* Product Listing */}
      <div className="flex flex-col md:flex-row gap-6">
        <aside className="md:w-56 shrink-0 space-y-2">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm">Categories</h4>
            <span className="text-xs text-muted-foreground">{categories.length} categories</span>
          </div>
          <ScrollReveal animate="fade-up" className="space-y-1">
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCat(c.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-all duration-200 ${
                  cat === c.id
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                {c.label}
              </button>
            ))}
          </ScrollReveal>
        </aside>
        
        <div className="flex-1 space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
            <Input
              leftIcon={Search}
              placeholder="Search products…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1"
            />
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Sort by:</label>
              <select
                className="px-3 py-1.5 text-sm border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Sort products"
              >
                <option value="featured">Featured</option>
                <option value="price-asc">Price: Low to High</option>
                <option value="price-desc">Price: High to Low</option>
                <option value="rating">Top Rated</option>
                <option value="newest">Newest</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {list.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <Search className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                <h3 className="font-display text-lg font-bold mb-2">No products found</h3>
                <p className="text-muted-foreground">Try adjusting your search or filters</p>
              </div>
            ) : (
              <StaggerContainer stagger={0.05}>
                {list.map((p, i) => (
                  <ScrollReveal key={p.id} animate="fade-up" delay={i * 0.05}>
                    <Card
                      hoverable
                      className="overflow-hidden group h-full flex flex-col"
                      padding="none"
                    >
                      <div className="relative aspect-square overflow-hidden bg-muted/30">
                        <img
                          src={PRODUCT_IMGS[i % PRODUCT_IMGS.length]}
                          alt={p.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          loading="lazy"
                          decoding="async"
                        />
                        {!p.inStock && (
                          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                            <Badge variant="danger" className="text-sm px-3 py-1">
                              Out of Stock
                            </Badge>
                          </div>
                        )}
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button className="h-8 w-8 rounded-full bg-background/90 backdrop-blur flex items-center justify-center shadow-md hover:bg-primary hover:text-primary-foreground transition-colors">
                            <ShoppingCart className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        {p.badge && (
                          <Badge
                            className="absolute top-2 left-2"
                            variant={p.badge === 'New' ? 'info' : p.badge === 'Sale' ? 'danger' : 'success'}
                          >
                            {p.badge}
                          </Badge>
                        )}
                      </div>
                      <div className="p-4 flex flex-col flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-semibold line-clamp-1">{p.name}</h3>
                          <Badge size="sm" variant="secondary">
                            {p.category}
                          </Badge>
                        </div>
                        <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                          <Star className="h-3.5 w-3.5 fill-primary text-primary" />
                          <span>{p.rating}</span>
                          <span className="text-muted-foreground/50">({p.reviews} reviews)</span>
                        </div>
                        <div className="mt-auto flex items-center justify-between pt-4 border-t border-border">
                          <span className="font-display text-lg font-bold">${p.price}</span>
                          <GlassButton
                            size="sm"
                            variant={p.inStock ? 'primary' : 'outline'}
                            disabled={!p.inStock}
                            rightIcon={ShoppingCart}
                          >
                            {p.inStock ? 'Add' : 'Notify Me'}
                          </GlassButton>
                        </div>
                      </div>
                    </Card>
                  </ScrollReveal>
                ))}
              </StaggerContainer>
            )}
          </div>
        </div>
      </div>
    </TemplateShell>
  );
}