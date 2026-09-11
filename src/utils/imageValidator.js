/**
 * Image validation utilities — ensures only real, production-grade assets are used.
 * Rejects AI-generated placeholders and invalid formats.
 */

const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif'];
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/svg+xml', 'image/gif'];

const REJECTED_PATTERNS = [
  /ai[-_]generated/i,
  /placeholder/i,
  /lorem/i,
  /dummy/i,
  /fake[-_]image/i,
  /generated[-_]by/i,
];

const MAX_FILE_SIZE_MB = 5;
const MIN_WIDTH = 100;
const MIN_HEIGHT = 100;

export function getExtension(filename) {
  const dot = filename.lastIndexOf('.');
  return dot >= 0 ? filename.slice(dot).toLowerCase() : '';
}

export function isAllowedExtension(filename) {
  return ALLOWED_EXTENSIONS.includes(getExtension(filename));
}

export function isRejectedFilename(filename) {
  return REJECTED_PATTERNS.some((pattern) => pattern.test(filename));
}

export function validateImageFile(file) {
  const errors = [];

  if (!file) {
    return { valid: false, errors: ['No file provided'] };
  }

  const name = file.name || '';
  const sizeMB = (file.size || 0) / (1024 * 1024);

  if (!isAllowedExtension(name)) {
    errors.push(`Invalid format. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
  }

  if (file.type && !ALLOWED_MIME_TYPES.includes(file.type)) {
    errors.push(`Invalid MIME type: ${file.type}`);
  }

  if (isRejectedFilename(name)) {
    errors.push('AI-generated or placeholder images are not allowed');
  }

  if (sizeMB > MAX_FILE_SIZE_MB) {
    errors.push(`File exceeds ${MAX_FILE_SIZE_MB}MB limit (${sizeMB.toFixed(1)}MB)`);
  }

  return { valid: errors.length === 0, errors, filename: name, sizeMB: sizeMB.toFixed(2) };
}

export function validateImageUrl(url) {
  const errors = [];

  if (!url || typeof url !== 'string') {
    return { valid: false, errors: ['Invalid URL'] };
  }

  try {
    const parsed = new URL(url, window.location.origin);
    const pathname = parsed.pathname;
    const ext = getExtension(pathname);

    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      errors.push(`URL must point to a real image (${ALLOWED_EXTENSIONS.join(', ')})`);
    }

    if (isRejectedFilename(pathname)) {
      errors.push('AI-generated or placeholder image URLs are rejected');
    }
  } catch {
    errors.push('Malformed URL');
  }

  return { valid: errors.length === 0, errors, url };
}

export function validateImageDimensions(width, height) {
  const errors = [];
  if (width < MIN_WIDTH) errors.push(`Width must be at least ${MIN_WIDTH}px`);
  if (height < MIN_HEIGHT) errors.push(`Height must be at least ${MIN_HEIGHT}px`);
  return { valid: errors.length === 0, errors, width, height };
}

export function validateImageAsset({ filename, path, source = 'local' }) {
  const errors = [];

  if (!filename) {
    return { valid: false, errors: ['Filename required'] };
  }

  if (!isAllowedExtension(filename)) {
    errors.push(`Invalid asset extension for: ${filename}`);
  }

  if (isRejectedFilename(filename) || (path && isRejectedFilename(path))) {
    errors.push(`Rejected asset (AI/placeholder detected): ${filename}`);
  }

  return {
    valid: errors.length === 0,
    errors,
    filename,
    source,
    isRealAsset: errors.length === 0,
  };
}

export const IMAGE_VALIDATION_RULES = {
  ALLOWED_EXTENSIONS,
  ALLOWED_MIME_TYPES,
  MAX_FILE_SIZE_MB,
  MIN_WIDTH,
  MIN_HEIGHT,
};
