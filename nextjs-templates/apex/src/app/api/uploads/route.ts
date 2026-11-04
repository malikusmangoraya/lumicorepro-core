import { prisma } from '@/lib/prisma';
import { created, fail, forbidden, serverError, unauthorized } from '@/lib/api';
import { getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic';

const MAX_BYTES = 3 * 1024 * 1024; // Vercel caps a function body at 4.5 MB.
const ALLOWED = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/avif', 'image/svg+xml']);

/**
 * POST /api/uploads — admin only, multipart form with a `file` field.
 *
 * The bytes go into the database because the deployment target has no writable
 * disk: a file written to public/ disappears with the next deploy. A real
 * product can swap this for S3/R2/Vercel Blob behind the same route.
 */
export async function POST(request: Request) {
  const session = await getSession().catch(() => null);
  if (!session) return unauthorized();
  if (session.role !== 'admin') return forbidden('Only an admin can upload media');

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return fail('INVALID_FORM', 'Send the file as multipart/form-data', 400);
  }

  const file = form.get('file');
  if (!(file instanceof File)) {
    return fail('NO_FILE', 'Attach an image in the "file" field', 400);
  }

  if (!ALLOWED.has(file.type)) {
    return fail(
      'UNSUPPORTED_TYPE',
      'Use a JPEG, PNG, WebP, AVIF or SVG image',
      415,
    );
  }

  if (file.size > MAX_BYTES) {
    return fail('FILE_TOO_LARGE', 'Images must be 3 MB or smaller', 413);
  }

  try {
    const bytes = Buffer.from(await file.arrayBuffer());
    const asset = await prisma.mediaAsset.create({
      data: {
        filename: file.name.slice(0, 200) || 'upload',
        mimeType: file.type,
        size: bytes.length,
        data: bytes,
      },
      select: { id: true, filename: true, mimeType: true, size: true },
    });

    return created(
      { ...asset, url: `/api/media/${asset.id}` },
      'Image uploaded',
    );
  } catch {
    return serverError('Could not store the image');
  }
}
