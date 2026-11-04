import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * A template is only usable if the reader can discover the configuration.
 * These assertions guard the two things that silently break that: the env
 * contract going missing, and a real .env being committed next to it.
 */
const root = path.resolve(__dirname, '..');

describe('environment contract', () => {
  it('ships a .env.example', () => {
    expect(existsSync(path.join(root, '.env.example'))).toBe(true);
  });

  it('documents every variable the app reads', () => {
    const example = readFileSync(path.join(root, '.env.example'), 'utf8');
    for (const key of [
      'DATABASE_URL',
      'JWT_SECRET',
      'JWT_REFRESH_SECRET',
      'NEXT_PUBLIC_SITE_URL',
    ]) {
      expect(example, `${key} must be documented in .env.example`).toContain(`${key}=`);
    }
  });

  it('keeps real env files out of git but allows the example', () => {
    const ignore = readFileSync(path.join(root, '.gitignore'), 'utf8');
    expect(ignore).toMatch(/^\.env$/m);
    expect(ignore).toMatch(/^\.env\.\*$/m);
    expect(ignore).toMatch(/^!\.env\.example$/m);
  });

  it('never ships a real secret in the example', () => {
    const example = readFileSync(path.join(root, '.env.example'), 'utf8');
    const jwt = example.match(/^JWT_SECRET=(.*)$/m)?.[1]?.trim() ?? '';
    expect(jwt).toBe('');
  });
});

describe('deployment config', () => {
  it('pins the Vercel framework preset so the build is not served as static output', () => {
    const config = JSON.parse(readFileSync(path.join(root, 'vercel.json'), 'utf8'));
    expect(config.framework).toBe('nextjs');
  });
});
