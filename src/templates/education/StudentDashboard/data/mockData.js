export const student = {
  name: 'Daniyal Ahmed',
  program: 'BS Computer Science · Semester 5',
  gpa: '3.72 / 4.00',
};

export const enrolled = [
  {
    name: 'Data Structures',
    progress: 68,
    due: 'Assignment 4 · Sep 16',
    grade: 'A-',
    img: 'course1',
    color: 'bg-primary',
  },
  {
    name: 'Linear Algebra',
    progress: 45,
    due: 'Quiz 2 · Sep 11',
    grade: 'B+',
    img: 'course2',
    color: 'bg-emerald-400',
  },
  {
    name: 'Operating Systems',
    progress: 82,
    due: 'Lab Report · Sep 14',
    grade: 'A',
    img: 'course3',
    color: 'bg-violet-400',
  },
  {
    name: 'Technical Writing',
    progress: 30,
    due: 'Draft · Sep 20',
    grade: '—',
    img: 'course4',
    color: 'bg-amber-400',
  },
];

export const upcoming = [
  { title: 'Quiz 2 — Linear Algebra', date: 'Sep 11 · 09:00 AM', type: 'Quiz', weight: '10%' },
  { title: 'Lab Report — OS Scheduling', date: 'Sep 14 · 11:59 PM', type: 'Lab', weight: '15%' },
  {
    title: 'Assignment 4 — DS Trees',
    date: 'Sep 16 · 05:00 PM',
    type: 'Assignment',
    weight: '12%',
  },
  { title: 'Midterm — Data Structures', date: 'Sep 22 · 10:00 AM', type: 'Exam', weight: '30%' },
];

export const activity = [
  { label: 'Study minutes this week', value: '412 min', delta: '+18%' },
  { label: 'Average quiz score', value: '86%', delta: '+4%' },
  { label: 'Lectures completed', value: '38 / 44', delta: '6 left' },
];
