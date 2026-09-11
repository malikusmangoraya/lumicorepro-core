import {
  BookOpen,
  GraduationCap,
  Timer,
  Trophy,
  CalendarDays,
  FileText,
  TrendingUp,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { student, enrolled, upcoming, activity } from './data/mockData';

const COURSE_IMGS = [
  img.education.course1,
  img.education.course2,
  img.education.course3,
  img.education.course4,
];

export default function StudentDashboard() {
  return (
    <TemplateShell
      title="Student Dashboard"
      description="Courses, deadlines, and a live picture of your semester."
      category="Education"
      actions={
        <Button size="sm">
          <BookOpen className="h-4 w-4 mr-1" />
          Browse Courses
        </Button>
      }
    >
      {/* Header */}
      <Card animate="fade-up" className="relative overflow-hidden mb-6">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/15 via-primary/5 to-transparent" />
        <div className="relative flex items-center gap-4 flex-wrap">
          <Avatar className="h-16 w-16">
            <img
              src={img.education.student}
              alt={student.name}
              className="h-full w-full object-cover"
            />
          </Avatar>
          <div className="flex-1 min-w-[180px]">
            <h3 className="font-display text-xl font-bold">{student.name}</h3>
            <p className="text-xs text-muted-foreground">{student.program}</p>
            <div className="flex gap-2 mt-2 flex-wrap">
              <Badge variant="secondary" size="sm" className="text-[10px]">
                CGPA {student.gpa}
              </Badge>
              <Badge variant="success" size="sm" className="text-[10px]">
                On-Track
              </Badge>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {activity.map((a) => (
              <div
                key={a.label}
                className="text-center rounded-xl bg-background/70 backdrop-blur px-3 py-2"
              >
                <p className="text-[10px] text-muted-foreground leading-tight">{a.label}</p>
                <p className="font-display font-bold text-sm">{a.value}</p>
                <p className="text-[10px] text-emerald-400 font-medium">{a.delta}</p>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Enrolled courses */}
        <div className="lg:col-span-2 space-y-6">
          <Card animate="fade-up">
            <h4 className="font-display font-bold mb-4 flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-primary" />
              Enrolled Courses
            </h4>
            <div className="space-y-3">
              {enrolled.map((c) => (
                <div
                  key={c.name}
                  className="flex items-center gap-4 rounded-xl border border-border p-3.5"
                >
                  <img
                    src={COURSE_IMGS[enrolled.indexOf(c) % COURSE_IMGS.length]}
                    alt={c.name}
                    className="h-14 w-14 rounded-xl object-cover shrink-0 hidden sm:block"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <p className="text-sm font-semibold">{c.name}</p>
                      <Badge variant="outline" className="text-[10px]">
                        {c.grade === '—' ? 'Ongoing' : `Current Grade ${c.grade}`}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-2">
                      <Progress value={c.progress} className={cn('h-1.5 flex-1', c.color)} />
                      <span className="text-xs font-bold shrink-0">{c.progress}%</span>
                    </div>
                    <div className="flex items-center gap-1 text-[11px] text-muted-foreground mt-1.5">
                      <CalendarDays className="h-3 w-3" />
                      {c.due}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={80}>
            <h4 className="font-display font-bold mb-4 flex items-center gap-2">
              <Timer className="h-5 w-5 text-amber-400" />
              Study Activity
            </h4>
            <div className="grid grid-cols-7 gap-2">
              {[34, 55, 0, 62, 78, 40, 22].map((min, i) => (
                <div key={i} className="flex flex-col items-center gap-1.5">
                  <div className="w-full h-16 rounded-lg bg-muted/60 flex items-end overflow-hidden">
                    <div
                      className={cn(
                        'w-full rounded-b-lg',
                        min
                          ? 'bg-gradient-to-t from-primary to-primary/50 bg-primary'
                          : 'bg-muted/30'
                      )}
                      style={{ height: `${(min / 78) * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'][i]}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-3 flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
              Peak focus: 06:30 PM – 09:00 PM
            </p>
          </Card>
        </div>

        {/* Upcoming */}
        <div className="space-y-6">
          <Card animate="fade-up" animationDelay={120}>
            <h4 className="font-display font-bold mb-4 flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-primary" />
              Upcoming Deadlines
            </h4>
            <div className="space-y-3">
              {upcoming.map((u) => (
                <div key={u.title} className="flex items-start gap-3">
                  <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold leading-snug">{u.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{u.date}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge variant="outline" className="text-[10px]">
                      {u.type}
                    </Badge>
                    <p className="text-[10px] text-muted-foreground mt-1">{u.weight}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={180} padding="sm" className="border-dashed">
            <h4 className="font-display font-bold mb-3 flex items-center gap-2">
              <Trophy className="h-4 w-4 text-amber-400" />
              This Week
            </h4>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li className="flex items-center gap-2">
                <Badge
                  variant="success"
                  size="sm"
                  className="h-5 w-5 rounded-full justify-center text-[10px]"
                >
                  ✓
                </Badge>
                All DS lectures watched
              </li>
              <li className="flex items-center gap-2">
                <Badge
                  variant="success"
                  size="sm"
                  className="h-5 w-5 rounded-full justify-center text-[10px]"
                >
                  ✓
                </Badge>
                Quiz 1 solved twice
              </li>
              <li className="flex items-center gap-2 text-muted-foreground/60">
                <Badge
                  variant="outline"
                  size="sm"
                  className="h-5 w-5 rounded-full justify-center text-[10px]"
                >
                  2
                </Badge>
                OS lab report draft pending
              </li>
            </ul>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
