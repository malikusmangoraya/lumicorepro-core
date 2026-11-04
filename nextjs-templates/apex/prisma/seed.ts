import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

const vehicles = [
  {
    slug: '2022-porsche-911-gt3',
    make: 'Porsche',
    model: '911 GT3',
    year: 2022,
    title: '2022 Porsche 911 GT3 (992)',
    description:
      'A 992-generation GT3 in GT Silver over black leather, specified with the six-speed manual and the Clubsport package. Single owner, full Porsche service history, and the 4.0-litre flat-six has never been tracked. Supplied with the original window sticker, two keys and the factory car cover.',
    price: 219500,
    currency: 'USD',
    mileage: 4200,
    mileageUnit: 'mi',
    bodyStyle: 'Coupe',
    fuelType: 'Petrol',
    transmission: '6-speed manual',
    locationCountry: 'United States',
    locationRegion: 'California',
    status: 'active',
    media: JSON.stringify([{ url: '/vehicles/2022-porsche-911-gt3.webp', alt: '2022 Porsche 911 GT3' }]),
    inspectionReferences: JSON.stringify([
      '180-point inspection, 14 March 2026 — no findings',
      'Paint depth: original on all panels',
      'DME over-rev report: range 1 only',
    ]),
    provenanceVerified: true,
    conditionNotes: 'Stone chips to the front bumper, photographed in the report. No paint work.',
    vin: 'WP0AC2A99NS200001',
    isFeatured: true,
  },
  {
    slug: '2019-ferrari-488-pista',
    make: 'Ferrari',
    model: '488 Pista',
    year: 2019,
    title: '2019 Ferrari 488 Pista',
    description:
      'Rosso Corsa over Nero Alcantara, with the optional carbon-fibre racing seats and the titanium exhaust. Ferrari Classiche documentation present, recent major service completed at an authorised dealer, and the car has covered fewer than 6,000 miles from new.',
    price: 429000,
    currency: 'USD',
    mileage: 5800,
    mileageUnit: 'mi',
    bodyStyle: 'Coupe',
    fuelType: 'Petrol',
    transmission: '7-speed dual-clutch',
    locationCountry: 'United States',
    locationRegion: 'Florida',
    status: 'active',
    media: JSON.stringify([{ url: '/vehicles/2019-ferrari-488-pista.webp', alt: '2019 Ferrari 488 Pista' }]),
    inspectionReferences: JSON.stringify([
      'Ferrari dealer major service, January 2026',
      'Classiche certification folder present',
      'Clutch wear measured at 18%',
    ]),
    provenanceVerified: true,
    conditionNotes: 'PPF to the front end. Two small stone chips beneath the film.',
    vin: 'ZFF90HLA0K0240002',
    isFeatured: true,
  },
  {
    slug: '2021-mclaren-720s',
    make: 'McLaren',
    model: '720S',
    year: 2021,
    title: '2021 McLaren 720S Performance',
    description:
      'Volcano Yellow with the Performance specification: carbon-fibre exterior packs, sports exhaust and the lightweight wheels. Two owners, McLaren service history, and a recent inspection with the active aero and suspension checked on the ramp.',
    price: 249000,
    currency: 'USD',
    mileage: 9100,
    mileageUnit: 'mi',
    bodyStyle: 'Coupe',
    fuelType: 'Petrol',
    transmission: '7-speed dual-clutch',
    locationCountry: 'United States',
    locationRegion: 'New York',
    status: 'active',
    media: JSON.stringify([{ url: '/vehicles/2021-mclaren-720s.webp', alt: '2021 McLaren 720S' }]),
    inspectionReferences: JSON.stringify([
      'McLaren service history, three stamps',
      'Active aero and suspension verified on ramp',
      'Tyres replaced at 8,400 miles',
    ]),
    provenanceVerified: true,
    conditionNotes: 'Front splitter has light road rash, visible in the photos.',
    vin: 'SBM14DCA0MW800003',
    isFeatured: true,
  },
  {
    slug: '2018-lamborghini-huracan-performante',
    make: 'Lamborghini',
    model: 'Huracán Performante',
    year: 2018,
    title: '2018 Lamborghini Huracán Performante',
    description:
      'Verde Mantis over Nero Ade, with the forged composite aero and the ALA system. Full Lamborghini service history, recent brake and tyre refresh, and the original delivery documentation from Sant’Agata.',
    price: 289500,
    currency: 'USD',
    mileage: 12400,
    mileageUnit: 'mi',
    bodyStyle: 'Coupe',
    fuelType: 'Petrol',
    transmission: '7-speed dual-clutch',
    locationCountry: 'United States',
    locationRegion: 'Texas',
    status: 'active',
    media: JSON.stringify([
      { url: '/vehicles/2018-lamborghini-huracan-performante.webp', alt: '2018 Lamborghini Huracán' },
    ]),
    inspectionReferences: JSON.stringify([
      'Lamborghini service history, four stamps',
      'ALA system function test passed',
      'Brake discs and pads replaced at 11,900 miles',
    ]),
    provenanceVerified: true,
    conditionNotes: 'Wheels show light kerb marks on the nearside front.',
    vin: 'ZHWUF4ZF0JLA00004',
    isFeatured: false,
  },
  {
    slug: '2020-aston-martin-vantage',
    make: 'Aston Martin',
    model: 'Vantage',
    year: 2020,
    title: '2020 Aston Martin Vantage',
    description:
      'Magnetic Silver over Obsidian leather with the sports exhaust and the premium audio upgrade. One owner, main-dealer service history, and a recent inspection covering the Mercedes-AMG-sourced powertrain.',
    price: 129000,
    currency: 'USD',
    mileage: 15600,
    mileageUnit: 'mi',
    bodyStyle: 'Coupe',
    fuelType: 'Petrol',
    transmission: '8-speed automatic',
    locationCountry: 'United States',
    locationRegion: 'Washington',
    status: 'active',
    media: JSON.stringify([{ url: '/vehicles/2020-aston-martin-vantage.webp', alt: '2020 Aston Martin Vantage' }]),
    inspectionReferences: JSON.stringify([
      'Aston Martin main-dealer service history',
      'Powertrain inspection, no faults stored',
      'All four tyres matched, 6 mm tread',
    ]),
    provenanceVerified: true,
    conditionNotes: 'Driver seat bolster shows light wear, consistent with mileage.',
    vin: 'SCFRMFAV0LGL00005',
    isFeatured: false,
  },
  {
    slug: '2017-audi-r8-v10-plus',
    make: 'Audi',
    model: 'R8 V10 Plus',
    year: 2017,
    title: '2017 Audi R8 V10 Plus',
    description:
      'Suzuka Grey over black with the carbon-fibre side blades and the Bang & Olufsen system. The 5.2-litre V10 with quattro and the S-tronic box, full Audi service history and a recent carbon-clean.',
    price: 118000,
    currency: 'USD',
    mileage: 22100,
    mileageUnit: 'mi',
    bodyStyle: 'Coupe',
    fuelType: 'Petrol',
    transmission: '7-speed dual-clutch',
    locationCountry: 'United States',
    locationRegion: 'Illinois',
    status: 'active',
    media: JSON.stringify([{ url: '/vehicles/2017-audi-r8-v10-plus.webp', alt: '2017 Audi R8 V10 Plus' }]),
    inspectionReferences: JSON.stringify([
      'Audi service history, six stamps',
      'Carbon clean completed February 2026',
      'Magnetic ride dampers checked, no leaks',
    ]),
    provenanceVerified: false,
    conditionNotes: 'Provenance from new is complete; one gap in 2019 is documented.',
    vin: 'WUAEAAFX0H7900006',
    isFeatured: false,
  },
];

const plans = [
  {
    name: 'Starter',
    slug: 'starter',
    amount: 24,
    interval: 'month',
    features: JSON.stringify([
      'Two vehicle history reports a month',
      'Pre-purchase checklist library',
      'Email support within 48 hours',
    ]),
    sortOrder: 1,
  },
  {
    name: 'Pro',
    slug: 'pro',
    amount: 64,
    interval: 'month',
    features: JSON.stringify([
      'Unlimited vehicle history reports',
      'Independent inspection coordination',
      'Private viewing scheduling',
      'Price alerts on saved searches',
    ]),
    isHighlight: true,
    sortOrder: 2,
  },
  {
    name: 'Enterprise',
    slug: 'enterprise',
    amount: 159,
    interval: 'month',
    features: JSON.stringify([
      'Everything in Pro',
      'Bulk provenance research',
      'Dedicated account specialist',
      'Custom reporting exports',
    ]),
    sortOrder: 3,
  },
];

const categories = [
  { name: 'Care kits', slug: 'care-kits', description: 'Detailing and paint protection' },
  { name: 'Driving gear', slug: 'driving-gear', description: 'Gloves, boots and helmets' },
  { name: 'Garage', slug: 'garage', description: 'Lifts, storage and tooling' },
];

const products = [
  { title: 'Ceramic coating kit', slug: 'ceramic-coating-kit', price: 189, stock: 24, categorySlug: 'care-kits', description: 'Two-stage ceramic kit with applicator and cure cloths.' },
  { title: 'Leather driving gloves', slug: 'leather-driving-gloves', price: 129, stock: 40, categorySlug: 'driving-gear', description: 'Perforated lambskin, unlined, with a snap wrist.' },
  { title: 'Aluminium race jack', slug: 'aluminium-race-jack', price: 349, stock: 8, categorySlug: 'garage', description: 'Low-profile 1.8-tonne jack with a rubber saddle.' },
];

async function main() {
  console.log('Seeding Apex…');

  for (const category of categories) {
    await prisma.category.upsert({
      where: { slug: category.slug },
      update: {},
      create: category,
    });
  }

  for (const plan of plans) {
    await prisma.plan.upsert({
      where: { slug: plan.slug },
      update: { amount: plan.amount, features: plan.features },
      create: plan,
    });
  }

  for (const vehicle of vehicles) {
    await prisma.vehicle.upsert({
      where: { slug: vehicle.slug },
      update: vehicle,
      create: vehicle,
    });
  }

  for (const product of products) {
    const category = await prisma.category.findUnique({ where: { slug: product.categorySlug } });
    const { categorySlug: _categorySlug, ...data } = product;
    await prisma.product.upsert({
      where: { slug: data.slug },
      update: {},
      create: {
        ...data,
        categoryId: category?.id,
        images: JSON.stringify([]),
        rating: 4.8,
        reviewCount: 12,
      },
    });
  }

  const passwordHash = await bcrypt.hash('Password123!', 12);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@apex.com' },
    update: { passwordHash },
    create: { email: 'admin@apex.com', name: 'Avery Admin', passwordHash, role: 'admin' },
  });

  const customer = await prisma.user.upsert({
    where: { email: 'customer@apex.com' },
    update: { passwordHash },
    create: { email: 'customer@apex.com', name: 'Casey Customer', passwordHash, role: 'customer' },
  });

  await prisma.inquiry.upsert({
    where: { idempotencyKey: 'seed-inquiry-0001' },
    update: {},
    create: {
      idempotencyKey: 'seed-inquiry-0001',
      userId: customer.id,
      vehicleId: (await prisma.vehicle.findUnique({ where: { slug: '2022-porsche-911-gt3' } }))?.id,
      name: 'Casey Customer',
      email: 'customer@apex.com',
      message: 'I would like to arrange a viewing of the GT3 this weekend, if it is still available.',
      consentGiven: true,
      consentAt: new Date(),
      status: 'new',
    },
  });

  // Demo orders across the lifecycle, so the admin Orders screen has something
  // to manage on a fresh install.
  const demoOrders = [
    {
      orderNumber: 'APX-2026-00001',
      customerEmail: 'customer@apex.com',
      vehicleSlug: '2022-porsche-911-gt3',
      status: 'pending',
      isPaid: false,
      isDelivered: false,
    },
    {
      orderNumber: 'APX-2026-00002',
      customerEmail: 'buyer.two@example.com',
      vehicleSlug: '2019-ferrari-488-pista',
      status: 'paid',
      isPaid: true,
      isDelivered: false,
    },
    {
      orderNumber: 'APX-2026-00003',
      customerEmail: 'buyer.three@example.com',
      vehicleSlug: '2021-mclaren-720s',
      status: 'shipped',
      isPaid: true,
      isDelivered: false,
      carrier: 'Enclosed Auto Transport',
      trackingNumber: 'EAT-889120',
    },
    {
      orderNumber: 'APX-2026-00004',
      customerEmail: 'buyer.four@example.com',
      vehicleSlug: '2017-audi-r8-v10-plus',
      status: 'delivered',
      isPaid: true,
      isDelivered: true,
      carrier: 'Enclosed Auto Transport',
      trackingNumber: 'EAT-771003',
    },
  ] as const;

  for (const demo of demoOrders) {
    const vehicle = await prisma.vehicle.findUnique({ where: { slug: demo.vehicleSlug } });
    if (!vehicle) continue;

    const existing = await prisma.order.findUnique({ where: { orderNumber: demo.orderNumber } });
    if (existing) continue;

    const total = Math.round(vehicle.price * 100) / 100;
    const order = await prisma.order.create({
      data: {
        orderNumber: demo.orderNumber,
        userId: demo.customerEmail === 'customer@apex.com' ? customer.id : null,
        customerEmail: demo.customerEmail,
        subtotal: total,
        tax: 0,
        shipping: 0,
        discount: 0,
        total,
        currency: vehicle.currency,
        status: demo.status,
        paymentMethod: demo.isPaid ? 'bank-transfer' : null,
        isPaid: demo.isPaid,
        isDelivered: demo.isDelivered,
        ...(('carrier' in demo) && demo.carrier ? { carrier: demo.carrier } : {}),
        ...(('trackingNumber' in demo) && demo.trackingNumber
          ? { trackingNumber: demo.trackingNumber }
          : {}),
        items: {
          create: [
            {
              title: vehicle.title,
              unitPrice: vehicle.price,
              quantity: 1,
              lineTotal: total,
            },
          ],
        },
      },
    });

    if (demo.isPaid) {
      await prisma.payment.create({
        data: {
          orderId: order.id,
          provider: 'bank-transfer',
          providerRef: `SEED-${demo.orderNumber}`,
          amount: total,
          currency: vehicle.currency,
          status: 'succeeded',
        },
      });
    }
  }

  await prisma.notification.create({
    data: {
      userId: admin.id,
      title: 'Seed complete',
      body: 'Demo vehicles, plans, orders and one enquiry are ready.',
      type: 'success',
    },
  });

  console.log('Done.');
  console.log('  admin@apex.com    / Password123!  (admin)');
  console.log('  customer@apex.com / Password123!  (customer)');
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
