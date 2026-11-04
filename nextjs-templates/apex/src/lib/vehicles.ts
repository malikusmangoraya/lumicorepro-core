import { prisma } from '@/lib/prisma';
import { parseJson } from '@/lib/utils';
import type { VehicleQuery } from '@/lib/validation';

export type VehicleMedia = { url: string; alt: string };

export type VehicleCardData = {
  id: string;
  slug: string;
  make: string;
  model: string;
  year: number;
  title: string;
  price: number;
  currency: string;
  mileage: number;
  mileageUnit: string;
  bodyStyle: string;
  transmission: string;
  locationCountry: string;
  locationRegion: string;
  provenanceVerified: boolean;
  media: VehicleMedia[];
};

export type VehicleDetailData = VehicleCardData & {
  description: string;
  fuelType: string;
  status: string;
  inspectionReferences: string[];
  conditionNotes: string | null;
  conditionReportUrl: string | null;
  vin: string | null;
};

export type VehicleListResult = {
  items: VehicleCardData[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
  makes: string[];
  databaseReady: boolean;
};

const CARD_SELECT = {
  id: true,
  slug: true,
  make: true,
  model: true,
  year: true,
  title: true,
  price: true,
  currency: true,
  mileage: true,
  mileageUnit: true,
  bodyStyle: true,
  transmission: true,
  locationCountry: true,
  locationRegion: true,
  provenanceVerified: true,
  media: true,
} as const;

type CardRow = {
  id: string;
  slug: string;
  make: string;
  model: string;
  year: number;
  title: string;
  price: number;
  currency: string;
  mileage: number;
  mileageUnit: string;
  bodyStyle: string;
  transmission: string;
  locationCountry: string;
  locationRegion: string;
  provenanceVerified: boolean;
  media: string;
};

function toCard(row: CardRow): VehicleCardData {
  return { ...row, media: parseJson<VehicleMedia[]>(row.media, []) };
}

function orderBy(sort: VehicleQuery['sort']) {
  switch (sort) {
    case 'price-asc':
      return { price: 'asc' as const };
    case 'price-desc':
      return { price: 'desc' as const };
    case 'mileage-asc':
      return { mileage: 'asc' as const };
    default:
      return { createdAt: 'desc' as const };
  }
}

/**
 * A template must build and run before its database exists, so a missing or
 * unmigrated database degrades to an empty, explicitly-labelled result rather
 * than a 500 on the storefront.
 */
export async function listVehicles(query: VehicleQuery): Promise<VehicleListResult> {
  const empty: VehicleListResult = {
    items: [],
    total: 0,
    page: 1,
    perPage: query.perPage,
    pages: 1,
    makes: [],
    databaseReady: false,
  };

  try {
    const where = {
      status: 'active' as const,
      ...(query.make ? { make: query.make } : {}),
      ...(query.priceMax ? { price: { lte: query.priceMax } } : {}),
      ...(query.q
        ? {
            OR: [
              { title: { contains: query.q } },
              { make: { contains: query.q } },
              { model: { contains: query.q } },
              { description: { contains: query.q } },
            ],
          }
        : {}),
    };

    const [rows, total, makes] = await Promise.all([
      prisma.vehicle.findMany({
        where,
        select: CARD_SELECT,
        orderBy: orderBy(query.sort),
        skip: (query.page - 1) * query.perPage,
        take: query.perPage,
      }),
      prisma.vehicle.count({ where }),
      prisma.vehicle.findMany({
        where: { status: 'active' },
        select: { make: true },
        distinct: ['make'],
        orderBy: { make: 'asc' },
      }),
    ]);

    return {
      items: rows.map(toCard),
      total,
      page: query.page,
      perPage: query.perPage,
      pages: Math.max(1, Math.ceil(total / query.perPage)),
      makes: makes.map((row) => row.make),
      databaseReady: true,
    };
  } catch {
    return empty;
  }
}

export async function getVehicleBySlug(slug: string): Promise<VehicleDetailData | null> {
  try {
    const row = await prisma.vehicle.findFirst({
      where: { slug, status: { in: ['active', 'reserved', 'sold'] } },
    });
    if (!row) return null;
    return {
      ...toCard(row),
      description: row.description,
      fuelType: row.fuelType,
      status: row.status,
      inspectionReferences: parseJson<string[]>(row.inspectionReferences, []),
      conditionNotes: row.conditionNotes,
      conditionReportUrl: row.conditionReportUrl,
      vin: row.vin,
    };
  } catch {
    return null;
  }
}

export async function listFeaturedVehicles(take = 3): Promise<VehicleCardData[]> {
  try {
    const rows = await prisma.vehicle.findMany({
      where: { status: 'active' },
      select: CARD_SELECT,
      orderBy: [{ isFeatured: 'desc' }, { createdAt: 'desc' }],
      take,
    });
    return rows.map(toCard);
  } catch {
    return [];
  }
}
