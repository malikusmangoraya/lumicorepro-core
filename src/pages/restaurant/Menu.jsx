/**
 * Menu — filterable food menu with categories, vegetarian/spicy filters,
 * add-to-cart, loading and error states.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Filter, X, Star, ShoppingCart, Utensils, Loader, RotateCcw } from 'lucide-react';
import { useCart } from '@/store/cartStore';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import api from '@/services/api';
import { cn } from '@/utils';
import { IMAGES } from './images';

const TAG_FILTERS = [
  { key: 'vegetarian', label: 'Vegetarian' },
  { key: 'vegan', label: 'Vegan' },
  { key: 'spicy', label: 'Spicy' },
];

export default function Menu() {
  const { t } = useTranslation();
  const { addItem, count } = useCart();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ category: 'all', tags: [] });

  const fetchMenu = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.category !== 'all') params.set('category', filters.category);
      filters.tags.forEach((tag) => params.append('tag', tag)); // not used server-side; kept for UI
      if (filters.tags.includes('vegetarian')) params.set('vegetarian', 'true');
      if (filters.tags.includes('vegan')) params.set('vegan', 'true');
      if (filters.tags.includes('spicy')) params.set('spicy', 'true');

      const [menuRes, catRes] = await Promise.all([
        api.get('/restaurant/menu', { params }),
        api.get('/restaurant/categories'),
      ]);
      setItems(menuRes.data.data || []);
      setCategories(catRes.data.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load menu. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchMenu();
  }, [fetchMenu]);

  const handleAdd = useCallback((item) => {
    addItem({
      id: item.id,
      name: item.title || item.name,
      price: Number(item.price),
      image: (item.images && item.images[0]) || item.image,
      qty: 1,
      serverId: item.id,
    });
    navigate('/restaurant/cart');
  }, [addItem, navigate]);

  const filteredItems = useMemo(() => items, [items]);

  return (
    <section className="min-h-screen bg-background text-foreground">
      <SEOPage title={t('restaurant.menu.title', 'Menu | Fresh Taste')} />

      <div className="container mx-auto px-4 py-8">
        {/* Header + cart count */}
        <div className="flex flex-col md:flex-row justify-between items-end gap-4 mb-10">
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight">{t('restaurant.menu.heading', 'Our Menu')}</h1>
            <p className="text-muted-foreground">{t('restaurant.menu.subhead', 'Freshly prepared, made to order')}</p>
          </div>
          <Link
            to="/restaurant/cart"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
          >
            <ShoppingCart className="h-5 w-5" />
            <span className="font-medium">{count} item{count !== 1 ? 's' : ''}</span>
          </Link>
        </div>

        {/* Error state */}
        {error && (
          <div className="mb-8 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
            <RotateCcw className="h-4 w-4 animate-spin" />
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={fetchMenu}>
              {t('common.retry', 'Retry')}
            </Button>
          </div>
        )}

        {/* Loading state */}
        {loading && !error && (
          <div className="mb-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i} className="h-96 flex flex-col items-center justify-center gap-4 opacity-50 animate-pulse">
                <Loader className="h-8 w-8" />
                <span className="text-muted-foreground text-sm">{t('common.loading', 'Loading…')}</span>
              </Card>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && filteredItems.length === 0 && (
          <div className="text-center py-20">
            <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Utensils className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-medium">{t('restaurant.menu.empty', 'No items found')}</h3>
            <p className="text-muted-foreground mt-2">{t('restaurant.menu.emptyDesc', 'Try adjusting your filters')}</p>
            <Button variant="outline" onClick={() => setFilters({ category: 'all', tags: [] })}>
              {t('common.clearFilters', 'Clear filters')}
            </Button>
          </div>
        )}

        {!loading && !error && filteredItems.length > 0 && (
          <>
            {/* Filters */}
            <div className="mb-8 flex flex-wrap gap-3 items-start">
              <div className="flex flex-col gap-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('restaurant.menu.category', 'Category')}
                </label>
                <div className="flex gap-2">
                  <Button
                    variant={filters.category === 'all' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setFilters({ ...filters, category: 'all' })}
                  >
                    {t('common.all', 'All')}
                  </Button>
                  {categories.map((cat) => (
                    <Button
                      key={cat}
                      variant={filters.category === cat ? 'primary' : 'outline'}
                      size="sm"
                      onClick={() => setFilters({ ...filters, category: cat })}
                    >
                      {cat}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('restaurant.menu.dietary', 'Dietary')}
                </label>
                <div className="flex gap-2">
                  {TAG_FILTERS.map((tag) => {
                    const active = filters.tags.includes(tag.key);
                    return (
                      <Button
                        key={tag.key}
                        variant={active ? 'secondary' : 'outline'}
                        size="sm"
                        onClick={() => {
                          const next = active
                            ? filters.tags.filter((t) => t !== tag.key)
                            : [...filters.tags, tag.key];
                          setFilters({ ...filters, tags: next });
                        }}
                      >
                        {tag.label}
                      </Button>
                    );
                  })}
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => setFilters({ category: 'all', tags: [] })}>
                <X className="h-4 w-4 mr-2" /> {t('common.clear', 'Clear')}
              </Button>
            </div>

            {/* Menu grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredItems.map((item) => {
                const tags = item.tags || [];
                const image = (item.images && item.images[0]) || item.image || IMAGES.fallback;
                return (
                  <Card key={item.id} className="group relative overflow-hidden hover:shadow-xl transition-shadow duration-300">
                    <div className="relative h-48 overflow-hidden">
                      <img
                        src={image}
                        alt={item.title || item.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        loading="lazy"
                      />
                      {tags.includes('vegetarian') && (
                        <Badge className="absolute top-2 left-2" variant="success">
                          {t('restaurant.veg', 'Veg')}
                        </Badge>
                      )}
                      {tags.includes('spicy') && (
                        <Badge className="absolute top-2 right-2" variant="warning">
                          {t('restaurant.spicy', 'Spicy')}
                        </Badge>
                      )}
                      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/70 to-transparent">
                        <span className="text-white font-semibold">{item.title || item.name}</span>
                        <span className="text-amber-300 text-sm font-bold">${Number(item.price).toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="p-5">
                      <p className="text-xs text-muted-foreground mb-1">{tags.filter((t) => !['vegetarian', 'spicy', 'vegan'].includes(t)).join(' · ') || t('restaurant.menu.popular', 'Popular')}</p>
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold group-hover:text-primary transition-colors">{item.title || item.name}</h3>
                        <div className="flex items-center gap-1">
                          <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                          <span className="text-xs font-medium">{item.rating ?? 4.5}</span>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                        {item.description || t('restaurant.menu.desc', 'Delicious and freshly prepared.')}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-bold">${Number(item.price).toFixed(2)}</span>
                        <Button
                          size="sm"
                          variant="outline"
                          leftIcon={ShoppingCart}
                          onClick={() => handleAdd(item)}
                          className="text-xs px-3 py-2"
                        >
                          {t('restaurant.menu.add', 'Add')}
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
