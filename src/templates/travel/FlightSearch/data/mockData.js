export const routes = ['KHI → LHE', 'KHI → ISB', 'KHI → AST', 'LHE → KHI'];

export const flights = [
  {
    airline: 'PAF Air',
    code: 'PK 301',
    dep: '08:15',
    arr: '09:40',
    dur: '1h 25m',
    stops: 0,
    price: 'Rs 12,400',
    type: 'Economy',
  },
  {
    airline: 'PAF Air',
    code: 'PK 302',
    dep: '14:20',
    arr: '15:45',
    dur: '1h 25m',
    stops: 0,
    price: 'Rs 14,900',
    type: 'Economy',
  },
  {
    airline: 'SkyLink',
    code: 'SL 507',
    dep: '07:00',
    arr: '09:05',
    dur: '2h 05m',
    stops: 1,
    price: 'Rs 9,800',
    type: 'Economy',
  },
  {
    airline: 'SkyLink',
    code: 'SL 510',
    dep: '19:40',
    arr: '21:50',
    dur: '2h 10m',
    stops: 1,
    price: 'Rs 10,200',
    type: 'Economy',
  },
  {
    airline: 'PAF Air',
    code: 'PK 310',
    dep: '10:30',
    arr: '11:55',
    dur: '1h 25m',
    stops: 0,
    price: 'Rs 21,500',
    type: 'Business',
  },
  {
    airline: 'MountainAir',
    code: 'MA 902',
    dep: '06:45',
    arr: '08:10',
    dur: '1h 25m',
    stops: 0,
    price: 'Rs 11,900',
    type: 'Economy',
  },
];

export const filters = {
  stops: ['All', 'Non-stop', '1 stop'],
  classes: ['All', 'Economy', 'Business'],
};
