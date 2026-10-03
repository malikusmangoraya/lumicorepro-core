import { useState } from 'react';
import { Star, Clock, Video, Calendar, MapPin, Phone, Search, Shield } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { doctors, specialties, stats, services } from './data/mockData';

const DOCTOR_IMGS = [
  img.healthcare.doctor1,
  img.healthcare.doctor2,
  img.healthcare.doctor3,
  img.healthcare.doctor4,
  img.healthcare.doctor5,
  img.healthcare.doctor6,
];

export default function MedicalPortal() {
  const [activeSpec, setActiveSpec] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = doctors.filter((d) => {
    const matchSpec = activeSpec === 'All' || d.specialty === activeSpec;
    const matchSearch =
      d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.specialty.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSpec && matchSearch;
  });

  return (
    <TemplateShell
      title="Medical Portal"
      description="Find doctors, book appointments & consult online."
      category="Healthcare"
      actions={
        <Button size="sm">
          <Phone className="h-4 w-4 mr-1" />
          Emergency
        </Button>
      }
    >
      {/* Hero with real image */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-64 mb-6">
        <img
          src={img.healthcare.hero}
          alt="Medical"
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchPriority="high"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/30 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <Badge variant="success" className="mb-2 w-fit">
            🏥 500+ Verified Doctors
          </Badge>
          <h2 className="font-display text-3xl font-bold text-white">Find Top Doctors Near You</h2>
          <p className="mt-1 text-white/80 text-sm max-w-xl">
            Book in-person visits or instant video consultations with verified specialists.
          </p>
          <div className="relative max-w-sm mt-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search doctor or specialty..."
              className="w-full rounded-xl border border-border bg-background/90 pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {stats.map((s, i) => (
          <Card
            key={i}
            animate="fade-up"
            animationDelay={i * 60}
            padding="sm"
            className="text-center hover-lift"
          >
            <p className="font-display text-2xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Specialty filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        {specialties.map((spec) => (
          <button
            key={spec}
            onClick={() => setActiveSpec(spec)}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium transition-all',
              activeSpec === spec
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                : 'bg-card border border-border text-muted-foreground hover:border-emerald-500/30'
            )}
          >
            {spec}
          </button>
        ))}
      </div>

      {/* Doctors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((doc, i) => (
          <Card key={doc.id} animate="fade-up" animationDelay={i * 60} className="hover-lift group">
            <div className="flex gap-4">
              <img
                src={DOCTOR_IMGS[i % DOCTOR_IMGS.length]}
                alt={doc.name}
                className="h-16 w-16 rounded-2xl object-cover shrink-0 ring-2 ring-border group-hover:ring-emerald-400/50 transition-all"
                loading="lazy"
                decoding="async"
              />
              <div className="flex-1 min-w-0">
                <h3 className="font-display font-bold text-sm truncate">{doc.name}</h3>
                <p className="text-xs text-primary">{doc.specialty}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{doc.hospital}</p>
                <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                    {doc.rating}
                  </span>
                  <span>{doc.exp}</span>
                  <span
                    className={cn(
                      'font-medium',
                      doc.available === 'Today' ? 'text-emerald-400' : 'text-amber-400'
                    )}
                  >
                    <Clock className="h-3 w-3 inline mr-0.5" />
                    {doc.available}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <span className="font-bold text-sm">{doc.fee}</span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="h-7 text-xs px-2">
                  <Video className="h-3 w-3 mr-1" />
                  Video
                </Button>
                <Button size="sm" className="h-7 text-xs px-2">
                  <Calendar className="h-3 w-3 mr-1" />
                  Book
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
