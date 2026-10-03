import { useState } from 'react';
import {
  MapPin,
  BedDouble,
  Bath,
  Ruler,
  Car,
  CalendarClock,
  Star,
  Phone,
  MessageCircle,
  Check,
  Building2,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar, Input } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { property, features, amenities, gallery, agent } from './data/mockData';

const GALLERY = [
  img.realestate.hero,
  img.realestate.interior,
  img.realestate.prop1,
  img.realestate.prop2,
  img.realestate.prop3,
];
const FEATURE_ICONS = [BedDouble, Bath, Ruler, Ruler, Car, CalendarClock];

export default function PropertyDetails() {
  const [active, setActive] = useState(0);

  return (
    <TemplateShell
      title={property.title}
      description={property.desc}
      category="Real Estate"
      actions={<Badge variant="success">{property.status}</Badge>}
    >
      {/* Gallery */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        <div className="relative overflow-hidden rounded-2xl border border-border sm:row-span-2 h-72 sm:h-auto min-h-[300px]">
          <img
            src={GALLERY[active]}
            alt={gallery[active]?.label || property.title}
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
            decoding="async"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
          <Badge className="absolute top-3 left-3 bg-primary/90">{property.type}</Badge>
          <div className="absolute bottom-3 left-3">
            <p className="font-display text-2xl font-bold text-white">{property.price}</p>
            <p className="text-white/70 text-xs">PKR · on seller's demand</p>
          </div>
        </div>
        {gallery.map((g, i) => (
          <button
            key={g.label}
            onClick={() => setActive(i)}
            className={cn(
              'relative overflow-hidden rounded-2xl border h-32 sm:h-36 transition-all',
              active === i
                ? 'ring-2 ring-primary border-primary'
                : 'border-border hover:border-primary/50'
            )}
          >
            <img
              src={GALLERY[i]}
              alt={g.label}
              className="absolute inset-0 w-full h-full object-cover"
              loading="lazy"
              decoding="async"
            />
            <span className="absolute bottom-2 left-2 bg-black/60 backdrop-blur px-2 py-0.5 rounded-full text-[11px] font-medium text-white">
              {g.label}
            </span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          <Card animate="fade-up">
            <div className="flex items-start justify-between gap-3 mb-3 flex-wrap">
              <div>
                <h3 className="font-display text-xl font-bold">{property.title}</h3>
                <p className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                  <MapPin className="h-4 w-4" />
                  {property.location}
                </p>
              </div>
              <span className="flex items-center gap-1 bg-amber-500/15 px-2.5 py-1 rounded-full text-sm font-bold text-amber-400">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                {property.rating}{' '}
                <span className="font-medium text-muted-foreground">({property.reviews})</span>
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{property.desc}</p>
          </Card>

          <Card animate="fade-up" animationDelay={60}>
            <h4 className="font-display font-bold mb-4">Key Specs</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {features.map((f, i) => {
                const Icon = FEATURE_ICONS[i % FEATURE_ICONS.length];
                return (
                  <div
                    key={f.label}
                    className="flex items-center gap-3 rounded-xl bg-muted/60 p-3.5"
                  >
                    <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Icon className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-[11px] text-muted-foreground">{f.label}</p>
                      <p className="text-sm font-bold">{f.value}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={120}>
            <h4 className="font-display font-bold mb-4">Amenities</h4>
            <div className="flex flex-wrap gap-2">
              {amenities.map((a) => (
                <span
                  key={a}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-muted text-xs font-medium"
                >
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  {a}
                </span>
              ))}
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card animate="fade-up" animationDelay={80}>
            <Avatar className="h-14 w-14 mx-auto mb-3">
              <img
                src={img.realestate.agent}
                alt={agent.name}
                className="h-full w-full object-cover"
                loading="lazy"
                decoding="async"
              />
            </Avatar>
            <h4 className="font-display font-bold text-center">{agent.name}</h4>
            <p className="text-center text-xs text-muted-foreground mb-1">{agent.role}</p>
            <p className="text-center text-xs text-emerald-400 font-semibold mb-4">
              {agent.response}
            </p>
            <div className="space-y-2">
              <Button className="w-full">
                <Phone className="h-4 w-4 mr-1" />
                {agent.phone}
              </Button>
              <Button className="w-full" variant="outline">
                <MessageCircle className="h-4 w-4 mr-1" />
                WhatsApp Agent
              </Button>
            </div>
            <p className="text-center text-[11px] text-muted-foreground mt-3">
              {agent.sold}+ properties sold
            </p>
          </Card>

          <Card animate="fade-up" animationDelay={140} padding="sm">
            <h4 className="font-display font-bold mb-3">Schedule a Visit</h4>
            <div className="space-y-2.5">
              <Input placeholder="Your name" />
              <Input type="date" defaultValue="2026-09-18" />
              <Button className="w-full" size="sm">
                <CalendarClock className="h-4 w-4 mr-1" />
                Request Site Visit
              </Button>
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={200} padding="sm">
            <div className="flex items-center gap-2 text-sm">
              <Building2 className="h-4 w-4 text-primary" />
              <span className="font-semibold">Verified Listing</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">
              Title documents verified by our legal team. EMI calculators available on request.
            </p>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
