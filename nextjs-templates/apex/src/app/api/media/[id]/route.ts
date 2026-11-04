import { prisma } from '@/lib/prisma';

/**
 * GET /api/media/:id — serve an uploaded image.
 *
 * Public on purpose: the URL is used by <img> tags on public pages. The id is a
 * cuid, so it is unguessable, and an asset never changes once written, hence the
 * immutable cache header.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    const asset = await prisma.mediaAsset.findUnique({ where: { id } });
    if (!asset) return new Response('Not found', { status: 404 });

    return new Response(new Uint8Array(asset.data), {
      status: 200,
      headers: {
        'Content-Type': asset.mimeType,
        'Content-Length': String(asset.size),
        'Cache-Control': 'public, max-age=31536000, immutable',
        'X-Content-Type-Options': 'nosniff',
        'Content-Disposition': 'inline',
        // An uploaded SVG can carry script; sandbox it so it cannot run here.
        'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; sandbox",
      },
    });
  } catch {
    return new Response('Not found', { status: 404 });
  }
}
