import { Star, GraduationCap, Award, BookOpen, Users } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { img } from '@/utils/images';
import { instructors, stats } from './data/mockData';

const COLORS = [
  'from-primary to-indigo-600',
  'from-emerald-500 to-teal-600',
  'from-amber-500 to-orange-600',
  'from-violet-500 to-purple-600',
  'from-rose-500 to-pink-600',
  'from-sky-500 to-blue-600',
];

function initials(name) {
  return name
    .replace(/^(Prof\.|Dr\.|Mr\.|Ms\.)\s*/, '')
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export default function InstructorDirectory() {
  return (
    <TemplateShell
      title="Learn From the Best"
      description="University-grade faculty, hand-picked for real-world teaching."
      category="Education"
      actions={
        <Button size="sm">
          <GraduationCap className="h-4 w-4 mr-1" />
          Become an Instructor
        </Button>
      }
    >
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {stats.map((s, i) => (
          <Card key={s.label} animate="fade-up" animationDelay={i * 60} padding="sm">
            <p className="font-display text-xl font-bold text-primary">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {instructors.map((t, i) => (
          <Card
            key={t.name}
            animate="fade-up"
            animationDelay={(i * 70) % 350}
            className="flex flex-col"
          >
            <div className="flex items-start gap-4 mb-4">
              <Avatar className="h-14 w-14">
                {i === 0 ? (
                  <img
                    src={img.education.student}
                    alt={t.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div
                    className={`h-full w-full flex items-center justify-center text-white font-display font-bold bg-gradient-to-br ${COLORS[i % COLORS.length]}`}
                  >
                    {initials(t.name)}
                  </div>
                )}
              </Avatar>
              <div className="min-w-0">
                <h3 className="font-display font-semibold leading-snug">{t.name}</h3>
                <p className="text-xs text-muted-foreground">{t.dept}</p>
                <p className="text-[11px] text-primary font-medium mt-0.5">
                  <Award className="h-3 w-3 inline mr-1" />
                  {t.cert}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="rounded-xl bg-muted/60 p-2 text-center">
                <p className="text-[11px] text-muted-foreground">Courses</p>
                <p className="text-sm font-bold">{t.courses}</p>
              </div>
              <div className="rounded-xl bg-muted/60 p-2 text-center">
                <p className="text-[11px] text-muted-foreground">Rating</p>
                <p className="text-sm font-bold text-amber-400">★ {t.rating}</p>
              </div>
              <div className="rounded-xl bg-muted/60 p-2 text-center">
                <p className="text-[11px] text-muted-foreground">Students</p>
                <p className="text-sm font-bold">{t.students}</p>
              </div>
            </div>
            <div className="mt-auto flex items-center gap-2 pt-3 border-t border-border/60">
              <Badge variant="outline" className="text-[10px]">
                <Users className="h-3 w-3 mr-1" />
                {t.exp} yrs teaching
              </Badge>
              <Button size="sm" className="ml-auto h-8 text-xs">
                <BookOpen className="h-3.5 w-3.5 mr-1" />
                View Courses
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Featured note */}
      <Card
        padding="sm"
        animate="fade-up"
        className="mt-6 flex items-center gap-3 flex-wrap border-dashed"
      >
        <Star className="h-5 w-5 text-amber-400 shrink-0" />
        <p className="text-sm text-muted-foreground flex-1 min-w-[220px]">
          Every instructor passes a{' '}
          <span className="font-semibold text-foreground">3-stage vetting</span> — academic record,
          live sample class, and student feedback pilot.
        </p>
        <Button size="sm" variant="outline" className="h-8 text-xs">
          See Vetting Process
        </Button>
      </Card>
    </TemplateShell>
  );
}
