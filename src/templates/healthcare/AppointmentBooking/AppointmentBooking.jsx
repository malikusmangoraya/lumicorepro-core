import { useState } from 'react';
import { CalendarDays, Clock, Stethoscope, Check, ShieldCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Input } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { departments, doctors, timeSlots, reasons } from './data/mockData';

const DOC_IMGS = {
  doctor1: img.healthcare.doctor1,
  doctor2: img.healthcare.doctor2,
  doctor3: img.healthcare.doctor3,
  doctor4: img.healthcare.doctor4,
  doctor5: img.healthcare.doctor5,
};

export default function AppointmentBooking() {
  const [dept, setDept] = useState('General Physician');
  const [doctor, setDoctor] = useState(doctors[1]);
  const [slot, setSlot] = useState(null);
  const [reason, setReason] = useState(reasons[0]);
  const [confirmed, setConfirmed] = useState(false);

  const available = doctors.filter((d) => d.dept === dept);

  return (
    <TemplateShell
      title="Book an Appointment"
      description="See a specialist today — pick a department, doctor, and time slot."
      category="Healthcare"
      actions={
        <Button size="sm">
          <CalendarDays className="h-4 w-4 mr-1" />
          My Appointments
        </Button>
      }
    >
      {/* Hero strip */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-44 mb-6">
        <img
          src={img.healthcare.hospital}
          alt="Hospital"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex items-end p-8">
          <div>
            <Badge className="mb-2 w-fit bg-emerald-500/90">
              <ShieldCheck className="h-3 w-3 mr-1" />
              Same-day slots available
            </Badge>
            <h2 className="font-display text-2xl font-bold text-white">
              Care, Booked in 60 Seconds
            </h2>
          </div>
        </div>
      </div>

      {confirmed ? (
        <Card animate="fade-up" className="text-center py-10 max-w-xl mx-auto">
          <div className="h-14 w-14 rounded-full bg-emerald-500/15 flex items-center justify-center mx-auto mb-4">
            <Check className="h-7 w-7 text-emerald-400" />
          </div>
          <h3 className="font-display text-2xl font-bold mb-2">Appointment Confirmed</h3>
          <p className="text-sm text-muted-foreground mb-1">
            {doctor.name} · {dept} · <span className="font-semibold text-foreground">{slot}</span>
          </p>
          <p className="text-xs text-muted-foreground mb-6">
            Reason: {reason}. You'll get an SMS reminder 2 hours before.
          </p>
          <Button variant="outline" onClick={() => setConfirmed(false)}>
            Book Another
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card animate="fade-up" className="lg:col-span-2">
            <h3 className="font-display font-bold mb-4">Choose Department</h3>
            <div className="flex flex-wrap gap-2 mb-6">
              {departments.map((d) => (
                <button
                  key={d}
                  onClick={() => {
                    setDept(d);
                    setDoctor(doctors.find((x) => x.dept === d) || doctors[0]);
                  }}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-xs font-medium transition-all border',
                    dept === d
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card border-border text-muted-foreground hover:border-primary/50'
                  )}
                >
                  {d}
                </button>
              ))}
            </div>

            <h3 className="font-display font-bold mb-4">Select Doctor</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
              {available.map((d) => (
                <button
                  key={d.name}
                  onClick={() => setDoctor(d)}
                  className={cn(
                    'flex items-center gap-3 rounded-2xl border p-3 text-left transition-all',
                    doctor?.name === d.name
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/40'
                  )}
                >
                  <img
                    src={DOC_IMGS[d.img]}
                    alt={d.name}
                    className="h-12 w-12 rounded-xl object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold truncate">{d.name}</p>
                    <p className="text-xs text-muted-foreground">{d.dept}</p>
                    <p className="text-xs text-emerald-400 font-medium mt-0.5">
                      {d.slot} · {d.fee}
                    </p>
                  </div>
                </button>
              ))}
            </div>

            <h3 className="font-display font-bold mb-3">Pick a Time Slot</h3>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 mb-5">
              {timeSlots.slice(0, 8).map((t) => (
                <button
                  key={t}
                  onClick={() => setSlot(t)}
                  className={cn(
                    'rounded-xl border px-2 py-2 text-xs font-medium transition-all',
                    slot === t
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card border-border hover:border-primary/50'
                  )}
                >
                  <Clock className="h-3 w-3 inline mr-1" />
                  {t}
                </button>
              ))}
            </div>

            <h3 className="font-display font-bold mb-3">Reason for Visit</h3>
            <div className="flex flex-wrap gap-2 mb-5">
              {reasons.map((r) => (
                <button
                  key={r}
                  onClick={() => setReason(r)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-xs font-medium transition-all border',
                    reason === r
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card border-border text-muted-foreground hover:border-primary/50'
                  )}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Patient name
                </label>
                <Input placeholder="e.g. Ayaan Raza" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Phone (for SMS)
                </label>
                <Input placeholder="03XX-XXXXXXX" />
              </div>
            </div>

            <Button size="lg" disabled={!doctor || !slot} onClick={() => setConfirmed(true)}>
              <Stethoscope className="h-4 w-4 mr-1" />
              Confirm Appointment
            </Button>
          </Card>

          {/* Summary card */}
          <Card animate="fade-up" animationDelay={100} className="h-fit sticky top-6">
            <h4 className="font-display font-bold mb-4">Appointment Summary</h4>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Department</span>
                <span className="font-semibold">{dept}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Doctor</span>
                <span className="font-semibold">{doctor?.name || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time</span>
                <span className="font-semibold">{slot || '—'}</span>
              </div>
              <div className="flex justify-between border-t border-border pt-3">
                <span className="text-muted-foreground">Consultation Fee</span>
                <span className="font-bold text-primary">{doctor?.fee}</span>
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground mt-4 leading-relaxed">
              Free rescheduling up to 3 hours before. 100% refund if cancelled 6 hours ahead.
            </p>
          </Card>
        </div>
      )}
    </TemplateShell>
  );
}
