export const plans = [
  {
    id: 1,
    name: 'Starter',
    price: 'PKR 2,500',
    period: '/month',
    features: ['Gym floor access', '1 PT session', 'Locker room', 'Basic nutrition guide'],
    highlighted: false,
  },
  {
    id: 2,
    name: 'Pro',
    price: 'PKR 5,000',
    period: '/month',
    features: [
      'Full gym access',
      '4 PT sessions',
      'Spa & sauna',
      'Custom meal plan',
      'Group classes',
    ],
    highlighted: true,
  },
  {
    id: 3,
    name: 'Elite',
    price: 'PKR 9,500',
    period: '/month',
    features: [
      '24/7 access',
      'Unlimited PT',
      'Nutrition coaching',
      'Body composition scan',
      'Priority booking',
      'Guest passes',
    ],
    highlighted: false,
  },
];

export const classes = [
  {
    name: 'HIIT Burn',
    time: '07:00 AM',
    trainer: 'Coach Bilal',
    spots: 8,
    intensity: 'High',
    duration: '45 min',
  },
  {
    name: 'Yoga Flow',
    time: '09:00 AM',
    trainer: 'Coach Maria',
    spots: 12,
    intensity: 'Low',
    duration: '60 min',
  },
  {
    name: 'Spin Cycle',
    time: '06:00 PM',
    trainer: 'Coach Asad',
    spots: 5,
    intensity: 'High',
    duration: '50 min',
  },
  {
    name: 'Kickboxing',
    time: '07:30 PM',
    trainer: 'Coach Hina',
    spots: 10,
    intensity: 'High',
    duration: '55 min',
  },
  {
    name: 'Pilates Core',
    time: '10:00 AM',
    trainer: 'Coach Sana',
    spots: 15,
    intensity: 'Medium',
    duration: '45 min',
  },
  {
    name: 'Strength 101',
    time: '05:00 PM',
    trainer: 'Coach Usman',
    spots: 6,
    intensity: 'Medium',
    duration: '60 min',
  },
];

export const trainers = [
  { name: 'Coach Bilal', specialty: 'HIIT & Cardio', exp: '8 yrs', clients: 120 },
  { name: 'Coach Maria', specialty: 'Yoga & Mindfulness', exp: '6 yrs', clients: 90 },
  { name: 'Coach Asad', specialty: 'Cycling & Endurance', exp: '5 yrs', clients: 75 },
  { name: 'Coach Hina', specialty: 'Kickboxing & Defense', exp: '7 yrs', clients: 95 },
];

export const stats = [
  { label: 'Active Members', value: '3,200+' },
  { label: 'Classes / Week', value: '84' },
  { label: 'Expert Trainers', value: '35+' },
  { label: 'Locations', value: '8' },
];
