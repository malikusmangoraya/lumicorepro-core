import { useState } from 'react';
import {
  CirclePlay,
  Check,
  Clock,
  Users,
  Star,
  BookOpen,
  Award,
  ChevronDown,
  ChevronUp,
  GraduationCap,
} from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { course, instructor, curriculum, outcomes, commitments } from './data/mockData';

export default function CourseDetails() {
  const [open, setOpen] = useState(0);

  return (
    <TemplateShell
      title={course.title}
      description={course.desc}
      category="Education"
      actions={
        <Badge variant="secondary">
          {course.category} · {course.level}
        </Badge>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Hero */}
          <Card animate="fade-up" className="overflow-hidden">
            <div className="relative h-56">
              <img
                src={img.education.hero}
                alt={course.title}
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
              <div className="absolute bottom-4 left-4 right-4">
                <div className="flex items-center gap-2 mb-2">
                  <Badge className="bg-rose-500/90">
                    <Star className="h-3 w-3 fill-amber-300 text-amber-300 mr-1" />
                    {course.rating}
                  </Badge>
                  <Badge variant="secondary" className="text-[10px]">
                    {course.students} students
                  </Badge>
                  <Badge variant="secondary" className="text-[10px]">
                    Updated {course.lastUpdated}
                  </Badge>
                </div>
                <h2 className="font-display text-2xl sm:text-3xl font-bold text-white leading-tight">
                  {course.title}
                </h2>
                <p className="text-white/80 text-sm mt-1">{course.language}</p>
              </div>
            </div>
          </Card>

          {/* Instructor */}
          <Card animate="fade-up" animationDelay={60}>
            <h3 className="font-display font-bold mb-4">Instructor</h3>
            <div className="flex items-center gap-4">
              <Avatar className="h-14 w-14 shrink-0">
                <img
                  src={img.education.student}
                  alt={instructor.name}
                  className="h-full w-full object-cover"
                />
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-display font-semibold">{instructor.name}</p>
                <p className="text-xs text-muted-foreground">{instructor.role}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {instructor.exp} · {instructor.students} students
                </p>
              </div>
              <Button size="sm" variant="outline" className="shrink-0">
                View Profile
              </Button>
            </div>
          </Card>

          {/* Outcomes */}
          <Card animate="fade-up" animationDelay={100}>
            <h3 className="font-display font-bold mb-4 flex items-center gap-2">
              <Award className="h-5 w-5 text-amber-400" />
              What You'll Gain
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {outcomes.map((o) => (
                <div key={o} className="flex items-start gap-2.5 text-sm">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  {o}
                </div>
              ))}
            </div>
          </Card>

          {/* Curriculum */}
          <Card animate="fade-up" animationDelay={140}>
            <h3 className="font-display font-bold mb-4 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-primary" />
              Course Curriculum · {course.lectures} lectures ({course.hours})
            </h3>
            <div className="space-y-3">
              {curriculum.map((m, i) => (
                <div key={m.module} className="rounded-2xl border border-border overflow-hidden">
                  <button
                    onClick={() => setOpen(open === i ? null : i)}
                    className={cn(
                      'w-full flex items-center gap-3 p-3.5 text-left transition-colors',
                      open === i && 'bg-muted/40'
                    )}
                  >
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <GraduationCap className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">{m.module}</p>
                      <p className="text-xs text-muted-foreground">
                        {m.lectures} lectures · {m.hours}
                      </p>
                    </div>
                    {open === i ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </button>
                  {open === i && (
                    <ul className="px-4 pb-4 space-y-1.5">
                      {m.items.map((item) => (
                        <li
                          key={item}
                          className="flex items-center gap-2 text-xs text-muted-foreground"
                        >
                          <CirclePlay className="h-3.5 w-3.5 text-primary shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6 h-fit lg:sticky lg:top-6">
          <Card animate="fade-up" animationDelay={80} className="overflow-hidden">
            <div className="relative h-40">
              <img
                src={img.education.course1}
                alt="Course preview"
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                <div className="h-14 w-14 rounded-full bg-white/90 flex items-center justify-center hover-lift">
                  <CirclePlay className="h-7 w-7 text-primary" />
                </div>
              </div>
              <Badge className="absolute top-3 left-3 bg-rose-500/90">{course.level}</Badge>
            </div>
            <div className="p-5">
              <div className="flex items-baseline gap-1 mb-4">
                <span className="font-display text-3xl font-bold">{course.price}</span>
                <span className="text-xs text-muted-foreground">
                  <s>Rs 6,000</s> 25% off
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-4">
                {commitments.map((c) => (
                  <div key={c.label} className="rounded-xl bg-muted/60 p-2.5 text-center">
                    <p className="text-[11px] text-muted-foreground">{c.label}</p>
                    <p className="text-sm font-bold">{c.value}</p>
                  </div>
                ))}
              </div>
              <Button size="lg" className="w-full mb-2">
                Enroll Now
              </Button>
              <Button size="lg" variant="outline" className="w-full">
                Add to Wishlist
              </Button>
              <div className="mt-4 space-y-1.5 text-xs text-muted-foreground">
                <p>• 30-day money-back guarantee</p>
                <p>• Certificate on completion</p>
                <p>• Access on mobile & TV</p>
              </div>
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={140} padding="sm">
            <h4 className="font-display font-bold mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              Weekly Commitments
            </h4>
            <Progress value={68} className="h-2 mb-3" />
            <p className="text-xs text-muted-foreground">
              Average learner finishes this course in 8 weeks at 4 hrs / week.
            </p>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
