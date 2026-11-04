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

export type VehicleFacets = {
  makes: string[];
  bodyStyles: string[];
  fuelTypes: string[];
  transmissions: string[];
};

export type VehicleListResult = {
  items: VehicleCardData[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
  facets: VehicleFacets;
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
    case 'year-desc':
      return { year: 'desc' as const };
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
    facets: { makes: [], bodyStyles: [], fuelTypes: [], transmissions: [] },
    databaseReady: false,
  };

  try {
    const where = {
      status: 'active' as const,
      ...(query.make ? { make: query.make } : {}),
      ...(query.bodyStyle ? { bodyStyle: query.bodyStyle } : {}),
      ...(query.fuelType ? { fuelType: query.fuelType } : {}),
      ...(query.transmission ? { transmission: query.transmission } : {}),
      ...(query.yearMin ? { year: { gte: query.yearMin } } : {}),
      ...(query.mileageMax !== undefined ? { mileage: { lte: query.mileageMax } } : {}),
      ...(query.priceMin || query.priceMax
        ? {
            price: {
              ...(query.priceMin ? { gte: query.priceMin } : {}),
              ...(query.priceMax ? { lte: query.priceMax } : {}),
            },
          }
        : {}),
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

    const activeOnly = { status: 'active' as const };
    const [rows, total, makes, bodyStyles, fuelTypes, transmissions] = await Promise.all([
      prisma.vehicle.findMany({
        where,
        select: CARD_SELECT,
        orderBy: orderBy(query.sort),
        skip: (query.page - 1) * query.perPage,
        take: query.perPage,
      }),
      prisma.vehicle.count({ where }),
      prisma.vehicle.findMany({
        where: activeOnly,
        select: { make: true },
        distinct: ['make'],
        orderBy: { make: 'asc' },
      }),
      prisma.vehicle.findMany({
        where: activeOnly,
        select: { bodyStyle: true },
        distinct: ['bodyStyle'],
        orderBy: { bodyStyle: 'asc' },
      }),
      prisma.vehicle.findMany({
        where: activeOnly,
        select: { fuelType: true },
        distinct: ['fuelType'],
        orderBy: { fuelType: 'asc' },
      }),
      prisma.vehicle.findMany({
        where: activeOnly,
        select: { transmission: true },
        distinct: ['transmission'],
        orderBy: { transmission: 'asc' },
      }),
    ]);

    return {
      items: rows.map(toCard),
      total,
      page: query.page,
      perPage: query.perPage,
      pages: Math.max(1, Math.ceil(total / query.perPage)),
      facets: {
        makes: makes.map((row) => row.make),
        bodyStyles: bodyStyles.map((row) => row.bodyStyle),
        fuelTypes: fuelTypes.map((row) => row.fuelType),
        transmissions: transmissions.map((row) => row.transmission),
      },
      databaseReady: true,
    };
  } catch {
    return empty;
  }
}

/**
 * Resolve an explicit list of slugs (saved cars, the compare tray, recently
 * viewed). Order follows the caller's list, not the database's.
 */
export async function getVehiclesBySlugs(slugs: string[]): Promise<VehicleCardData[]> {
  const wanted = [...new Set(slugs.filter(Boolean))].slice(0, 24);
  if (wanted.length === 0) return [];
  try {
    const rows = await prisma.vehicle.findMany({
      where: { slug: { in: wanted }, status: { in: ['active', 'reserved', 'sold'] } },
      select: CARD_SELECT,
    });
    const bySlug = new Map(rows.map((row) => [row.slug, toCard(row)]));
    return wanted
      .map((slug) => bySlug.get(slug))
      .filter((vehicle): vehicle is VehicleCardData => Boolean(vehicle));
  } catch {
    return [];
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
