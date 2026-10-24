/**
 * RestaurantHome — hero with optional video background, featured menu,
 * special offers/daily deals, WhatsApp CTA and Google Maps location.
 * Warm food-photography aesthetic, mobile-first, SEO-optimized.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import {
  Play, MapPin, Phone, Clock, Star, CheckCircle2, RotateCcw,
  Flame, MessageCircle, Utensils,
} from 'lucide-react';
import { useCart } from '@/store/cartStore';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import SEO from '@/components/common/SEO';
import { cn } from '@/utils';
import { IMAGES } from './images';

const FEATURED = [
  { id: 'm1', name: 'Margherita Pizza', price: 12.99, image: IMAGES.pizza, tags: ['vegetarian'], rating: 4.8 },
  { id: 'm2', name: 'Classic Cheeseburger', price: 10.99, image: IMAGES.burger, tags: [], rating: 4.6 },
  { id: 'm3', name: 'Pasta Alfredo', price: 14.50, image: IMAGES.pasta, tags: ['vegetarian'], rating: 4.7 },
  { id: 'm4', name: 'Greek Salad', price: 9.00, image: IMAGES.salad, tags: ['vegetarian', 'vegan'], rating: 4.5 },
];

const DEALS = [
  { id: 'd1', title: 'Lunch Combo', subtitle: 'Any main + drink + side', price: 15.99, image: IMAGES.burger },
  { id: 'd2', title: 'Pizza Night', subtitle: '2 large pizzas + garlic bread', price: 24.99, image: IMAGES.pizza },
  { id: 'd3', title: 'Family Feast', subtitle: 'Serves 4 — pasta, salad & dessert', price: 39.99, image: IMAGES.pasta },
];

export default function RestaurantHome() {
  const { t } = useTranslation();
  const { addItem } = useCart();
  const navigate = useNavigate();
  const [videoReady, setVideoReady] = useState(false);

  const handleAdd = useCallback((item) => {
    addItem({
      id: item.id,
      name: item.name,
      price: item.price,
      image: item.image,
      qty: 1,
      serverId: item.id,
    });
  }, [addItem]);

  return (
    <section className="min-h-screen flex flex-col bg-background text-foreground">
      <SEO
        title={t('restaurant.home.title', 'Fresh Taste | Restaurant & Online Ordering')}
        description={t('restaurant.home.desc', 'Warm, modern restaurant with online ordering, table reservations and daily deals. Order food online in minutes.')}
        openGraph={{
          images: [{ url: IMAGES.hero, width: 1600, height: 900, alt: 'Restaurant hero' }],
        }}
      />

      {/* ── Hero ── */}
      <div className="relative h-[70svh] min-h-[500px] overflow-hidden rounded-none">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
          aria-hidden="true"
          onLoadedData={() => setVideoReady(true)}
        >
          <source src="https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
        {!videoReady && (
          <div className="absolute inset-0 bg-amber-900/40">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3 animate-pulse">
                <div className="w-12 h-12 rounded-full border-4 border-amber-400 border-t-transparent animate-spin" />
                <span className="text-sm text-amber-100">{t('restaurant.home.loading', 'Preparing…')}</span>
              </div>
            </div>
          </div>
        )}
        <div className="relative z-10 flex flex-col items-center justify-center h-full text-center px-4">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-300 text-xs font-semibold border border-amber-500/20">
              <Flame className="h-3 w-3" /> {t('restaurant.home.new', 'New')}
            </span>
          <h1 className="mt-6 text-4xl md:text-6xl font-display font-extrabold tracking-tight text-white drop-shadow-md">
            {t('restaurant.home.headline', 'Good Food, Good Mood')}
          </h1>
          <p className="mt-4 text-lg md:text-xl text-amber-100/90 max-w-2xl mx-auto drop-shadow">
            {t('restaurant.home.subhead', 'Fresh ingredients, warm hospitality and fast online ordering. Book a table or order for delivery today.')}
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button
              size="lg"
              leftIcon={Utensils}
              onClick={() => navigate('/restaurant/menu')}
              className="bg-amber-600 hover:bg-amber-700 text-white shadow-lg"
            >
              {t('restaurant.home.viewMenu', 'View Menu')}
            </Button>
            <Button
              size="lg"
              variant="outline"
              leftIcon={ClockIcon}
              onClick={() => navigate('/restaurant/reservation')}
              className="border-white/20 hover:border-white text-white hover:bg-white/10"
            >
              {t('restaurant.home.reserveTable', 'Reserve Table')}
            </Button>
          </div>
          <div className="mt-8 flex items-center gap-3 text-amber-200 text-sm">
            <MapPin className="h-4 w-4" /> <span>{t('restaurant.home.address', '123 Taste Street, Flavor City')}</span>
            <span className="w-px h-3 bg-amber-400/40 mx-1" aria-hidden="true" />
            <Phone className="h-4 w-4" /> <span>+1 (555) 123-4567</span>
          </div>
        </div>
      </div>

      {/* ── Featured Menu ── */}
      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
            <div>
              <h2 className="text-3xl font-display font-bold tracking-tight">{t('restaurant.home.featured', 'Featured Dishes')}</h2>
              <p className="text-muted-foreground">{t('restaurant.home.featuredDesc', "Today's chef recommendations")}</p>
            </div>
            <Link
              to="/restaurant/menu"
              className="text-sm font-medium text-primary hover:underline"
            >
              {t('restaurant.home.seeAll', 'See all menu →')}
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURED.map((item) => (
              <Card key={item.id} className="group overflow-hidden hover:shadow-xl transition-shadow duration-300">
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={item.image}
                    alt={item.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                  <Badge
                    className="absolute top-2 left-2"
                    variant={item.tags.includes('vegetarian') ? 'success' : 'default'}
                  >
                    {item.tags.includes('vegetarian') ? t('restaurant.veg', 'Veg') : t('restaurant.sig', 'Signature')}
                  </Badge>
                  <div className="absolute top-2 right-2 flex flex-col gap-1">
                    <span className="bg-black/60 text-white px-2 py-0.5 rounded text-xs font-semibold">
                      ${item.price.toFixed(2)}
                    </span>
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400 drop-shadow" />
                    <span className="text-xs font-semibold text-amber-100">{item.rating}</span>
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="font-semibold group-hover:text-primary transition-colors">{item.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{item.tags.join(', ') || t('restaurant.home.popular', 'Customer favorite')}</p>
                  <Button
                    size="sm"
                    variant="outline"
                    fullWidth
                    onClick={() => handleAdd(item)}
                    className="mt-3"
                  >
                    {t('restaurant.home.addToCart', 'Add to Cart')}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ── Special Offers / Daily Deals ── */}
      <section className="py-16 bg-amber-50 dark:bg-amber-900/20 border-y border-border">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-display font-bold tracking-tight">{t('restaurant.home.deals', 'Special Offers')}</h2>
            <p className="text-muted-foreground mt-2">{t('restaurant.home.dealsDesc', 'Daily deals for dine-in and takeaway')}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {DEALS.map((deal) => (
              <Card key={deal.id} className="relative overflow-hidden group">
                <div className="h-48 overflow-hidden">
                  <img
                    src={deal.image}
                    alt={deal.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                  <Badge className="absolute top-2 left-2" variant="warning">
                    {t('restaurant.home.limited', 'Limited')}
                  </Badge>
                </div>
                <div className="p-5">
                  <h3 className="font-semibold">{deal.title}</h3>
                  <p className="text-sm text-muted-foreground">{deal.subtitle}</p>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xl font-bold text-primary">${deal.price.toFixed(2)}</span>
                    <Button size="sm" leftIcon={Utensils} onClick={() => navigate('/restaurant/menu')}>
                      {t('restaurant.home.orderNow', 'Order')}
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ── Contact / Location CTA ── */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center bg-white dark:bg-card p-8 rounded-2xl shadow-sm border border-border">
            <div>
              <h2 className="text-2xl font-display font-bold">{t('restaurant.home.visitUs', 'Visit Us')}</h2>
              <p className="text-muted-foreground mt-4">{t('restaurant.home.visitDesc', 'We’re located in the heart of the city. Come taste the difference or order online for fast delivery.')}</p>
              <div className="mt-6 space-y-4">
                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-primary mt-0.5" />
                  <div>
                    <p className="font-medium">{t('restaurant.home.address', '123 Taste Street, Flavor City')}</p>
                    <p className="text-sm text-muted-foreground">Open daily 7:00 AM – 11:00 PM</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Phone className="h-5 w-5 text-primary mt-0.5" />
                  <div>
                    <p className="font-medium">+1 (555) 123-4567</p>
                    <p className="text-sm text-muted-foreground">Call for reservations</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-primary mt-0.5" />
                  <div>
                    <p className="font-medium">Mon–Sun: 7am–11pm</p>
                    <p className="text-sm text-muted-foreground">Last order 10:30 PM</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="relative h-64 rounded-xl overflow-hidden shadow-lg border border-border">
              <iframe
                title={t('restaurant.home.map', 'Restaurant location')}
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3022.16!2d-73.9882!3d40.7488!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c25855c6489699%3A0x55194ec5a1ae072e!2sTimes%20Square!5e0!3m2!1sen!2sus!4v1600000000000!5m2!1sen!2sus"
                width="100%"
                height="100%"
                style={{ border: 0 }}
                loading="lazy"
                allowFullScreen=""
                aria-label={t('restaurant.home.map', 'Restaurant location')}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── WhatsApp floating order button ── */}
      <a
        href="https://wa.me/15551234567?text=Hi%2C%20I%20would%20like%20to%20place%20an%20order"
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-[#25D366] text-white px-5 py-3 rounded-full shadow-lg hover:bg-[#128C7E] transition-all animate-bounce"
        aria-label={t('restaurant.home.whatsapp', 'Order on WhatsApp')}
      >
        <MessageCircle className="h-5 w-5" />
        <span className="font-medium hidden sm:block">{t('restaurant.home.whatsappOrder', 'WhatsApp Order')}</span>
      </a>
    </section>
  );
}
