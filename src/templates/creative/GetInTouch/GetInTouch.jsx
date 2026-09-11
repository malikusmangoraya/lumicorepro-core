import { useState } from 'react';
import { MapPin, Mail, Phone, Clock, Send, CircleCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Input, Textarea } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { studio, services, budgetOptions } from './data/mockData';

const INFO = [
  { icon: MapPin, label: 'Studio', value: studio.location },
  { icon: Mail, label: 'Email', value: studio.email },
  { icon: Phone, label: 'Phone', value: studio.phone },
  { icon: Clock, label: 'Hours', value: studio.hours },
];

export default function GetInTouch() {
  const [service, setService] = useState(services[0]);
  const [sent, setSent] = useState(false);

  return (
    <TemplateShell
      title="Start Something"
      description="A conversation costs nothing. A great brand costs this much less than you think."
      category="Creative"
      actions={
        <Badge variant="success">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          Booking Q4
        </Badge>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <Card animate="fade-up" className="lg:col-span-3">
          {sent ? (
            <div className="text-center py-14">
              <CircleCheck className="h-12 w-12 text-emerald-400 mx-auto mb-4" />
              <h3 className="font-display text-2xl font-bold mb-2">Inquiry Sent</h3>
              <p className="text-sm text-muted-foreground mb-5">
                We'll reply within one business day with next steps.
              </p>
              <Button variant="outline" onClick={() => setSent(false)}>
                Send Another
              </Button>
            </div>
          ) : (
            <>
              <h3 className="font-display text-lg font-bold mb-5">New Project Inquiry</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">
                    Name
                  </label>
                  <Input placeholder="Your name" />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">
                    Email
                  </label>
                  <Input type="email" placeholder="you@brand.com" />
                </div>
              </div>
              <div className="mb-4">
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  What do you need?
                </label>
                <div className="flex flex-wrap gap-2">
                  {services.map((s) => (
                    <button
                      key={s}
                      onClick={() => setService(s)}
                      className={cn(
                        'px-3 py-1.5 rounded-full text-xs font-medium transition-all border',
                        service === s
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-card border-border text-muted-foreground hover:border-primary/50'
                      )}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              <div className="mb-4">
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Budget
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {budgetOptions.map((b) => (
                    <button
                      key={b}
                      className="rounded-xl border border-border bg-card py-2 text-xs font-medium hover:border-primary/50 transition-all"
                    >
                      {b}
                    </button>
                  ))}
                </div>
              </div>
              <div className="mb-5">
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  About the project
                </label>
                <Textarea rows={5} placeholder="Goals, timeline, must-haves…" />
              </div>
              <Button size="lg" onClick={() => setSent(true)}>
                <Send className="h-4 w-4 mr-1" />
                Send Inquiry
              </Button>
            </>
          )}
        </Card>

        {/* Studio info */}
        <div className="lg:col-span-2 space-y-6">
          <Card animate="fade-up" animationDelay={80}>
            <div className="relative h-36 overflow-hidden rounded-xl mb-4">
              <img src={img.creative.hero} alt="Studio" className="h-full w-full object-cover" />
              <div className="absolute inset-0 bg-black/30" />
              <h4 className="absolute bottom-3 left-3 font-display text-lg font-bold text-white">
                MuddyStudio
              </h4>
            </div>
            <div className="space-y-3">
              {INFO.map((info) => {
                const Icon = info.icon;
                return (
                  <div key={info.label} className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                      <Icon className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">{info.label}</p>
                      <p className="text-sm font-semibold truncate">{info.value}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card
            animate="fade-up"
            animationDelay={140}
            padding="sm"
            className="border-dashed flex items-center gap-3"
          >
            <img
              src={img.creative.team1}
              alt="Team"
              className="h-12 w-12 rounded-xl object-cover shrink-0"
            />
            <p className="text-xs text-muted-foreground leading-relaxed">
              <span className="font-semibold text-foreground">Prefer a quick call?</span> Mondays
              and Thursdays 2–4 PM are our open hours.
            </p>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
