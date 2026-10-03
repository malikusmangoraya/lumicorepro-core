import {
  Mic,
  Video,
  MonitorUp,
  MessageCircle,
  PhoneOff,
  Send,
  Check,
  FileText,
  Pill,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { doctor, chat, controls } from './data/mockData';

const CONTROL_ICONS = [Mic, Video, MonitorUp, MessageCircle, PhoneOff];
const CONTROL_TONES = {
  0: 'text-foreground',
  1: 'text-foreground',
  2: 'text-foreground',
  3: 'text-foreground',
  4: 'bg-rose-600 text-white border-rose-600',
};

export default function TelehealthRoom() {
  return (
    <TemplateShell
      title="Video Consultation"
      description="A live telehealth room — video call, secure chat, and shared screen."
      category="Healthcare"
      actions={
        <Badge variant="success">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          Live Session
        </Badge>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video area */}
        <Card animate="fade-up" className="lg:col-span-2 overflow-hidden relative">
          <div className="relative h-[420px]">
            <img
              src={img.healthcare.doctor1}
              alt={doctor.name}
              className="absolute inset-0 w-full h-full object-cover"
              loading="lazy"
              decoding="async"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />

            {/* Timer */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur px-3 py-1 rounded-full text-xs font-medium text-white flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" /> 12:47 elapsed
            </div>

            {/* Doctor label */}
            <div className="absolute bottom-4 left-4 flex items-center gap-3">
              <Avatar className="h-12 w-12 ring-2 ring-white/40">
                <img
                  src={img.healthcare.doctor1}
                  alt={doctor.name}
                  className="h-full w-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
              </Avatar>
              <div>
                <p className="font-display font-bold text-white">{doctor.name}</p>
                <p className="text-white/70 text-xs">{doctor.role}</p>
              </div>
            </div>
            <Badge variant="secondary" className="absolute bottom-4 right-4 text-[10px]">
              <Check className="h-3 w-3 mr-1 text-emerald-400" />
              Encrypted & End-to-end
            </Badge>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-3 p-4 flex-wrap">
            {controls.map((c, i) => {
              const Icon = CONTROL_ICONS[i];
              return (
                <button
                  key={c.label}
                  aria-label={c.label}
                  className={cn(
                    'h-12 w-12 rounded-xl border border-border bg-card flex items-center justify-center transition-all hover:border-primary/50',
                    CONTROL_TONES[i]
                  )}
                >
                  <Icon className="h-5 w-5" />
                </button>
              );
            })}
            <span className="sr-only">Call controls</span>
          </div>
        </Card>

        {/* Chat */}
        <Card animate="fade-up" animationDelay={80} className="flex flex-col">
          <h3 className="font-display font-bold mb-4 flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-primary" />
            In-Call Chat
          </h3>
          <div className="flex-1 space-y-3 overflow-hidden mb-4">
            {chat.map((m, i) => (
              <div
                key={i}
                className={cn('flex', m.from === 'patient' ? 'justify-end' : 'justify-start')}
              >
                <div
                  className={cn(
                    'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed',
                    m.from === 'patient'
                      ? 'bg-primary text-primary-foreground rounded-br-sm'
                      : 'bg-muted rounded-bl-sm'
                  )}
                >
                  {m.text}
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-2 pt-3 border-t border-border">
            <input
              placeholder="Type a message..."
              className="flex-1 rounded-xl border border-border bg-card px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <Button className="h-10 w-10 p-0" aria-label="Send message">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>

      {/* Post-call actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
        {[
          {
            icon: Pill,
            title: 'ePrescription',
            desc: 'Medicines sent directly to your pharmacy.',
            variant: 'default',
          },
          {
            icon: FileText,
            title: 'Visit Summary',
            desc: 'Notes & doctor recommendations (PDF).',
            variant: 'outline',
          },
          {
            icon: Check,
            title: 'Mark Complete',
            desc: 'Finish the consultation and rate it.',
            variant: 'outline',
          },
        ].map((a, i) => {
          const Icon = a.icon;
          return (
            <Card
              key={a.title}
              animate="fade-up"
              animationDelay={i * 60}
              padding="sm"
              className="flex items-center gap-3 hover-lift"
            >
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold">{a.title}</p>
                <p className="text-xs text-muted-foreground">{a.desc}</p>
              </div>
            </Card>
          );
        })}
      </div>
    </TemplateShell>
  );
}
