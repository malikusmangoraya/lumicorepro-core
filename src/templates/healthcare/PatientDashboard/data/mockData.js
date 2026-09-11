export const patient = {
  name: 'Ayaan Raza',
  age: 34,
  blood: 'O+',
  weight: '72 kg',
  height: '5\u20329\u2033',
  insurance: 'State Life — Active',
  memberSince: '2021',
};

export const vitals = [
  { label: 'Heart Rate', value: '72', unit: 'bpm', delta: '+2', good: true },
  { label: 'Blood Pressure', value: '118/76', unit: 'mmHg', delta: '-4', good: true },
  { label: 'Blood Sugar', value: '98', unit: 'mg/dL', delta: '+6', good: true },
  { label: 'Oxygen Saturation', value: '98', unit: '%', delta: '0', good: true },
];

export const appointments = [
  {
    type: 'Cardiology — Dr. Ayesha Siddiqui',
    date: 'Mon, Sep 14 · 10:30 AM',
    status: 'Upcoming',
    dept: 'Cardiology',
  },
  {
    type: 'Lab — CBC & Lipid Panel',
    date: 'Sat, Sep 12 · 08:00 AM',
    status: 'Upcoming',
    dept: 'Lab',
  },
  {
    type: 'General Checkup — Dr. Bilal Khan',
    date: 'Aug 28 · 11:00 AM',
    status: 'Completed',
    dept: 'Physician',
  },
  { type: 'Dental Cleaning', date: 'Jul 15 · 03:00 PM', status: 'Completed', dept: 'Dental' },
];

export const medications = [
  {
    name: 'Metformin 500mg',
    dose: '1 tab after breakfast',
    schedule: 'Daily · 08:00 AM',
    days: 'Repeats',
    taken: true,
  },
  {
    name: 'Atorvastatin 10mg',
    dose: '1 tab at night',
    schedule: 'Daily · 09:00 PM',
    days: '21 days left',
    taken: false,
  },
  {
    name: 'Vitamin D3 2000 IU',
    dose: '1 tab with meal',
    schedule: 'Daily · 01:00 PM',
    days: 'Repeats',
    taken: true,
  },
];
