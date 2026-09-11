import {
  Briefcase,
  GraduationCap,
  Mail,
  Phone,
  MapPin,
  Link2,
  Download,
  Wrench,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { profile, experience, education, skillSets } from './data/mockData';

const CONTACT_ICONS = [MapPin, Mail, Phone, Link2];

export default function ResumeTimeline() {
  return (
    <TemplateShell
      title="Daniyal Ahmed — Résumé"
      description={profile.tagline}
      category="Portfolio"
      actions={
        <Button size="sm">
          <Download className="h-4 w-4 mr-1" />
          Download CV
        </Button>
      }
    >
      {/* Header */}
      <Card animate="fade-up" className="relative overflow-hidden mb-8">
        <div className="absolute inset-0 bg-gradient-to-r from-teal-500/15 via-primary/5 to-transparent" />
        <div className="relative flex items-center gap-5 flex-wrap">
          <Avatar className="h-20 w-20 ring-4 ring-background">
            <img
              src={img.portfolio.avatar}
              alt={profile.name}
              className="h-full w-full object-cover"
            />
          </Avatar>
          <div className="flex-1 min-w-[200px]">
            <h2 className="font-display text-2xl font-bold">{profile.name}</h2>
            <p className="text-primary font-medium text-sm">{profile.title}</p>
            <p className="text-xs text-muted-foreground mt-1.5 max-w-lg leading-relaxed">
              {profile.tagline}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {profile.contacts.map((c, i) => {
              const Icon = CONTACT_ICONS[i % CONTACT_ICONS.length];
              return (
                <span
                  key={c}
                  className="flex items-center gap-2 rounded-xl bg-background/70 backdrop-blur px-3 py-2 text-xs font-medium"
                >
                  <Icon className="h-3.5 w-3.5 text-primary shrink-0" />
                  {c}
                </span>
              );
            })}
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Experience timeline */}
          <Card animate="fade-up">
            <h3 className="font-display font-bold mb-5 flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-primary" />
              Experience
            </h3>
            <div className="relative space-y-6 pl-5">
              <div className="absolute left-1.5 top-1.5 bottom-1.5 w-px bg-border" />
              {experience.map((job) => (
                <div key={job.role + job.company} className="relative">
                  <span className="absolute -left-5 top-1.5 h-3 w-3 rounded-full bg-primary ring-4 ring-primary/15" />
                  <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                    <h4 className="font-display font-semibold">
                      {job.role} <span className="text-muted-foreground">· {job.company}</span>
                    </h4>
                    <Badge variant="outline" className="text-[10px]">
                      {job.period}
                    </Badge>
                  </div>
                  <ul className="space-y-1 mt-1.5">
                    {job.points.map((pt) => (
                      <li key={pt} className="text-sm text-muted-foreground flex gap-2">
                        <span className="text-primary">•</span>
                        {pt}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Card>

          {/* Education */}
          <Card animate="fade-up" animationDelay={60}>
            <h3 className="font-display font-bold mb-4 flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-primary" />
              Education
            </h3>
            {education.map((ed) => (
              <div key={ed.degree} className="flex items-center justify-between gap-3 flex-wrap">
                <div>
                  <p className="font-semibold">{ed.degree}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{ed.school}</p>
                </div>
                <div className="text-right">
                  <Badge variant="success" className="text-[10px]">
                    {ed.grade}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-1">{ed.period}</p>
                </div>
              </div>
            ))}
          </Card>
        </div>

        {/* Skills sidebar */}
        <div className="space-y-6">
          <Card animate="fade-up" animationDelay={100}>
            <h3 className="font-display font-bold mb-4 flex items-center gap-2">
              <Wrench className="h-5 w-5 text-primary" />
              Skills
            </h3>
            <div className="space-y-4">
              {skillSets.map((s) => (
                <div key={s.label}>
                  <p className="text-xs font-semibold text-muted-foreground mb-2">{s.label}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {s.skills.map((k) => (
                      <Badge key={k} variant="outline" size="sm" className="text-[11px]">
                        {k}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={140} padding="sm" className="border-dashed">
            <p className="text-sm font-semibold mb-1">Open to</p>
            <p className="text-xs text-muted-foreground">
              Senior roles, freelance projects, or a CTO seat at a sensible startup.
            </p>
            <Button className="w-full mt-3" size="sm">
              Let's Talk
            </Button>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
