import {
  HeartPulse,
  Activity,
  Droplets,
  Wind,
  CalendarDays,
  Pill,
  Clock,
  Check,
  ShieldCheck,
  Plus,
  FileText,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { patient, vitals, appointments, medications } from './data/mockData';

const VITAL_ICONS = [HeartPulse, Activity, Droplets, Wind];
const STATUS_TONE = { Upcoming: 'primary', Completed: 'secondary' };

export default function PatientDashboard() {
  return (
    <TemplateShell
      title="Patient Dashboard"
      description="Your health at a glance — vitals, appointments, and medications in one place."
      category="Healthcare"
      actions={
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1" />
          New Appointment
        </Button>
      }
    >
      {/* Header card */}
      <Card animate="fade-up" className="relative overflow-hidden mb-6">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/15 via-primary/5 to-transparent" />
        <div className="relative flex items-center gap-4 flex-wrap">
          <Avatar className="h-16 w-16">
            <img
              src={img.healthcare.doctor5}
              alt={patient.name}
              className="h-full w-full object-cover"
            />
          </Avatar>
          <div className="flex-1 min-w-[180px]">
            <h3 className="font-display text-xl font-bold">{patient.name}</h3>
            <p className="text-xs text-muted-foreground">
              Age {patient.age} · {patient.blood} · {patient.weight} · {patient.height}
            </p>
            <Badge variant="success" size="sm" className="mt-2 text-[10px]">
              <ShieldCheck className="h-3 w-3 mr-1" />
              {patient.insurance}
            </Badge>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center rounded-xl bg-background/70 backdrop-blur px-4 py-2">
              <p className="text-[11px] text-muted-foreground">Member Since</p>
              <p className="font-display font-bold text-sm">{patient.memberSince}</p>
            </div>
            <div className="text-center rounded-xl bg-background/70 backdrop-blur px-4 py-2">
              <p className="text-[11px] text-muted-foreground">Appointments</p>
              <p className="font-display font-bold text-sm">24</p>
            </div>
            <div className="text-center rounded-xl bg-background/70 backdrop-blur px-4 py-2">
              <p className="text-[11px] text-muted-foreground">Next Checkup</p>
              <p className="font-display font-bold text-sm">Sep 14</p>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Vitals */}
          <Card animate="fade-up">
            <h4 className="font-display font-bold mb-4 flex items-center gap-2">
              <HeartPulse className="h-5 w-5 text-rose-400" />
              Latest Vitals
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {vitals.map((v, i) => {
                const Icon = VITAL_ICONS[i];
                return (
                  <div key={v.label} className="rounded-xl bg-muted/60 p-3.5">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className={cn('h-4 w-4', i === 0 ? 'text-rose-400' : 'text-primary')} />
                      <span className="text-[11px] text-muted-foreground">{v.label}</span>
                    </div>
                    <p className="font-display text-lg font-bold">
                      {v.value}{' '}
                      <span className="text-[10px] text-muted-foreground font-medium">
                        {v.unit}
                      </span>
                    </p>
                    <p
                      className={cn(
                        'text-[11px] font-medium mt-1',
                        v.good ? 'text-emerald-400' : 'text-amber-400'
                      )}
                    >
                      {v.delta} than last week
                    </p>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Appointments */}
          <Card animate="fade-up" animationDelay={80}>
            <h4 className="font-display font-bold mb-4 flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-primary" />
              Appointments
            </h4>
            <div className="space-y-3">
              {appointments.map((a) => (
                <div
                  key={a.type}
                  className="flex items-center gap-4 rounded-xl border border-border p-3.5"
                >
                  <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                    <CalendarDays className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate">{a.type}</p>
                    <p className="text-xs text-muted-foreground">{a.date}</p>
                  </div>
                  <Badge variant={STATUS_TONE[a.status]} className="text-[10px]">
                    {a.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          {/* Medications */}
          <Card animate="fade-up" animationDelay={120}>
            <h4 className="font-display font-bold mb-4 flex items-center gap-2">
              <Pill className="h-5 w-5 text-emerald-400" />
              Current Medications
            </h4>
            <div className="space-y-3">
              {medications.map((m) => (
                <div
                  key={m.name}
                  className="flex items-center gap-4 rounded-xl border border-border p-3.5"
                >
                  <div
                    className={cn(
                      'h-10 w-10 rounded-xl flex items-center justify-center shrink-0',
                      m.taken ? 'bg-emerald-500/15' : 'bg-amber-500/15'
                    )}
                  >
                    {m.taken ? (
                      <Check className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <Clock className="h-5 w-5 text-amber-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{m.name}</p>
                      <Badge variant="outline" className="text-[10px]">
                        {m.days}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {m.dose} · {m.schedule}
                    </p>
                  </div>
                  <div className="sm:hidden" />
                  <Progress value={m.taken ? 100 : 60} className="w-16 sm:w-24 h-1.5 shrink-0" />
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card animate="fade-up" animationDelay={140} padding="sm">
            <h4 className="font-display font-bold mb-3">Health Score</h4>
            <div className="text-center mb-4">
              <div className="h-28 w-28 mx-auto rounded-full bg-gradient-to-br from-emerald-500/20 to-teal-500/10 flex items-center justify-center relative">
                <div className="h-24 w-24 rounded-full bg-card flex flex-col items-center justify-center">
                  <span className="font-display text-2xl font-bold">87</span>
                  <span className="text-[10px] text-muted-foreground">/100</span>
                </div>
              </div>
              <p className="text-sm font-semibold mt-2">Good — Keep It Up</p>
              <p className="text-[11px] text-muted-foreground">Improved 4 points this month</p>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full w-[87%] bg-gradient-to-r from-emerald-400 to-teal-400" />
            </div>
            <p className="text-[11px] text-muted-foreground mt-2">
              Scores across diet, activity & sleep
            </p>
          </Card>

          <Card animate="fade-up" animationDelay={200} padding="sm">
            <h4 className="font-display font-bold mb-3">Recent Reports</h4>
            <ul className="space-y-2.5 text-sm">
              {['CBC + Lipid Panel — Aug 28', 'ECG — Aug 01', 'Nutrition Assessment — Jul 12'].map(
                (r) => (
                  <li key={r} className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary shrink-0" />
                    <span className="text-xs">{r}</span>
                  </li>
                )
              )}
            </ul>
            <Button size="sm" variant="outline" className="w-full mt-3 h-8 text-xs">
              View All Reports
            </Button>
          </Card>

          <Card animate="fade-up" animationDelay={260} padding="sm" className="border-dashed">
            <p className="text-sm font-semibold mb-1">Rx Renewal Due</p>
            <p className="text-xs text-muted-foreground mb-3">Atorvastatin renews in 7 days.</p>
            <Button size="sm" className="w-full h-8 text-xs">
              Request Renewal
            </Button>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
