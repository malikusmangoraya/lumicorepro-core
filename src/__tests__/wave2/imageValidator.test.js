import { describe, expect, it } from 'vitest';
import {
  getExtension,
  IMAGE_VALIDATION_RULES,
  isAllowedExtension,
  isRejectedFilename,
  validateImageAsset,
  validateImageDimensions,
  validateImageFile,
  validateImageUrl,
} from '../../utils/imageValidator';

const file = (overrides = {}) => ({
  name: 'hero.webp',
  type: 'image/webp',
  size: 1024 * 1024,
  ...overrides,
});

describe('imageValidator — extensions and names', () => {
  it('extracts lower-cased extensions', () => {
    expect(getExtension('Photo.JPEG')).toBe('.jpeg');
    expect(getExtension('archive.tar.gz')).toBe('.gz');
    expect(getExtension('no-extension')).toBe('');
  });

  it('allows only real image extensions', () => {
    ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif'].forEach((ext) => {
      expect(isAllowedExtension(`image${ext}`)).toBe(true);
    });
    expect(isAllowedExtension('image.bmp')).toBe(false);
    expect(isAllowedExtension('document.pdf')).toBe(false);
  });

  it('rejects placeholder and AI-generated filenames', () => {
    [
      'ai-generated-hero.jpg',
      'ai_generated-hero.jpg',
      'placeholder.png',
      'lorem-ipsum.jpg',
      'dummy-image.png',
      'fake-image.jpg',
      'generated-by-ai.jpg',
    ].forEach((name) => {
      expect(isRejectedFilename(name)).toBe(true);
    });
    expect(isRejectedFilename('team-photo.jpg')).toBe(false);
  });
});

describe('imageValidator — files', () => {
  it('accepts a normal image under the size limit', () => {
    const result = validateImageFile(file());

    expect(result).toEqual({ valid: true, errors: [], filename: 'hero.webp', sizeMB: '1.00' });
  });

  it('rejects a missing file', () => {
    expect(validateImageFile(null)).toEqual({ valid: false, errors: ['No file provided'] });
  });

  it('rejects disallowed extensions and MIME types', () => {
    const result = validateImageFile(file({ name: 'invoice.pdf', type: 'application/pdf' }));

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(2);
    expect(result.errors[0]).toContain('Invalid format');
    expect(result.errors[1]).toBe('Invalid MIME type: application/pdf');
  });

  it('rejects files larger than 5MB', () => {
    const result = validateImageFile(file({ size: 6 * 1024 * 1024 }));

    expect(result.valid).toBe(false);
    expect(result.errors).toEqual(['File exceeds 5MB limit (6.0MB)']);
  });

  it('allows a file at exactly the 5MB boundary', () => {
    expect(validateImageFile(file({ size: 5 * 1024 * 1024 })).valid).toBe(true);
  });

  it('rejects placeholder filenames', () => {
    const result = validateImageFile(file({ name: 'placeholder-hero.png', type: 'image/png' }));

    expect(result.valid).toBe(false);
    expect(result.errors).toEqual(['AI-generated or placeholder images are not allowed']);
  });

  it('accepts files with no browser-reported MIME type', () => {
    expect(validateImageFile(file({ type: '' })).valid).toBe(true);
  });
});

describe('imageValidator — URLs', () => {
  it('accepts absolute and root-relative image URLs', () => {
    expect(validateImageUrl('https://cdn.example.com/hero.webp').valid).toBe(true);
    expect(validateImageUrl('/images/hero.webp')).toEqual({
      valid: true,
      errors: [],
      url: '/images/hero.webp',
    });
  });

  it('rejects URLs without an image extension', () => {
    const result = validateImageUrl('https://cdn.example.com/api/hero');

    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain('URL must point to a real image');
  });

  it('rejects placeholder URLs case-insensitively', () => {
    const result = validateImageUrl('https://cdn.example.com/PLACEHOLDER.PNG');

    expect(result.valid).toBe(false);
    expect(result.errors).toEqual(['AI-generated or placeholder image URLs are rejected']);
  });

  it('handles malformed and non-string URLs', () => {
    expect(validateImageUrl('http://exa mple.com/hero.png')).toEqual({
      valid: false,
      errors: ['Malformed URL'],
      url: 'http://exa mple.com/hero.png',
    });
    expect(validateImageUrl(null)).toEqual({ valid: false, errors: ['Invalid URL'] });
    expect(validateImageUrl(42)).toEqual({ valid: false, errors: ['Invalid URL'] });
  });
});

describe('imageValidator — dimensions and assets', () => {
  it('enforces minimum dimensions of 100x100', () => {
    expect(validateImageDimensions(100, 100)).toEqual({
      valid: true,
      errors: [],
      width: 100,
      height: 100,
    });
    expect(validateImageDimensions(99, 100).errors).toEqual(['Width must be at least 100px']);
    expect(validateImageDimensions(100, 50).errors).toEqual(['Height must be at least 100px']);
    expect(validateImageDimensions(20, 20).errors).toHaveLength(2);
  });

  it('validates asset descriptors and flags real assets', () => {
    expect(validateImageAsset({ filename: 'hero.jpg' })).toEqual({
      valid: true,
      errors: [],
      filename: 'hero.jpg',
      source: 'local',
      isRealAsset: true,
    });

    expect(validateImageAsset({ filename: '' })).toEqual({
      valid: false,
      errors: ['Filename required'],
    });
  });

  it('rejects bad extensions and placeholder paths in assets', () => {
    expect(validateImageAsset({ filename: 'logo.bmp' }).errors).toEqual([
      'Invalid asset extension for: logo.bmp',
    ]);

    const rejected = validateImageAsset({
      filename: 'hero.jpg',
      path: 'src/assets/ai-generated/hero.jpg',
      source: 'cdn',
    });
    expect(rejected.valid).toBe(false);
    expect(rejected.isRealAsset).toBe(false);
    expect(rejected.errors).toEqual(['Rejected asset (AI/placeholder detected): hero.jpg']);
    expect(rejected.source).toBe('cdn');
  });

  it('exposes the validation rules', () => {
    expect(IMAGE_VALIDATION_RULES).toEqual({
      ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif'],
      ALLOWED_MIME_TYPES: [
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/svg+xml',
        'image/gif',
      ],
      MAX_FILE_SIZE_MB: 5,
      MIN_WIDTH: 100,
      MIN_HEIGHT: 100,
    });
  });
});
