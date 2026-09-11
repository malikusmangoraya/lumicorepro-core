import { useState } from 'react';
import { Star, Phone, CalendarDays, Stethoscope, ShieldCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { doctors, specialties, stats } from './data/mockData';

const DOC_IMGS = {
  doctor1: img.healthcare.doctor1,
  doctor2: img.healthcare.doctor2,
  doctor3: img.healthcare.doctor3,
  doctor4: img.healthcare.doctor4,
  doctor5: img.healthcare.doctor5,
};

export default function DoctorDirectory() {
  const [specialty, setSpecialty] = useState('All');
  const list = specialty === 'All' ? doctors : doctors.filter((d) => d.specialty === specialty);

  return (
    <TemplateShell
      title="Find a Doctor"
      description="Verified consultants, honest ratings, transparent fees."
      category="Healthcare"
      actions={
        <Button size="sm">
          <Stethoscope className="h-4 w-4 mr-1" />
          Need Urgent Help? ER Open 24/7
        </Button>
      }
    >
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {stats.map((s, i) => (
          <Card key={s.label} animate="fade-up" animationDelay={i * 60} padding="sm">
            <p className="font-display text-xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        {specialties.map((s) => (
          <button
            key={s}
            onClick={() => setSpecialty(s)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              specialty === s
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {list.map((d, i) => (
          <Card
            key={d.name}
            animate="fade-up"
            animationDelay={(i * 70) % 350}
            className="overflow-hidden"
          >
            <div className="relative h-40">
              <img src={DOC_IMGS[d.img]} alt={d.name} className="h-full w-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
              <Badge className="absolute top-3 left-3 bg-rose-500/90">
                <Stethoscope className="h-3 w-3 mr-1" />
                {d.specialty}
              </Badge>
              {!d.available && (
                <Badge variant="secondary" className="absolute top-3 right-3">
                  Booked Calendar
                </Badge>
              )}
              <div className="absolute bottom-3 left-3">
                <p className="font-display font-bold text-white">{d.name}</p>
                <p className="text-white/70 text-xs">{d.exp} yrs experience</p>
              </div>
            </div>
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="flex items-center gap-1 text-xs font-bold text-amber-400">
                  <Star className="h-3.5 w-3.5 fill-amber-400" />
                  {d.rating}
                </span>
                <span className="text-xs text-muted-foreground">· {d.patients} patients</span>
                <Badge
                  variant={d.available ? 'success' : 'secondary'}
                  size="sm"
                  className="ml-auto text-[10px]"
                >
                  {d.available ? 'Available Today' : 'Closed'}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mb-3">{d.hospital}</p>
              <div className="flex items-center justify-between pt-3 border-t border-border/60">
                <span className="text-sm font-bold text-primary">
                  {d.fee}
                  <span className="text-[10px] text-muted-foreground font-medium"> /visit</span>
                </span>
                <div className="flex gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 w-8 p-0"
                    aria-label={`Call clinic`}
                  >
                    <Phone className="h-3.5 w-3.5" />
                  </Button>
                  <Button size="sm" className="h-8 text-xs">
                    <CalendarDays className="h-3.5 w-3.5 mr-1" />
                    Book
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card
        padding="sm"
        animate="fade-up"
        className="mt-6 flex items-center gap-3 flex-wrap border-dashed"
      >
        <ShieldCheck className="h-5 w-5 text-emerald-400 shrink-0" />
        <p className="text-sm text-muted-foreground flex-1 min-w-[220px]">
          Every listed doctor is{' '}
          <span className="font-semibold text-foreground">PMDC-registered</span> and carries
          verified credentials on file.
        </p>
        <Button size="sm" variant="outline" className="h-8 text-xs">
          Licensed & Verified
        </Button>
      </Card>
    </TemplateShell>
  );
}
