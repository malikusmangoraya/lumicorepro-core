import { readFileSync, existsSync, readdirSync } from 'node:fs';
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

describe('layouts', () => {
  const app = path.join(root, 'src', 'app');
  const read = (relative: string) => readFileSync(path.join(app, relative), 'utf8');

  it('keeps site chrome out of the auth screens', () => {
    const auth = read(path.join('(auth)', 'layout.tsx'));
    expect(auth).not.toContain('SiteHeader');
    expect(auth).not.toContain('SiteFooter');
  });

  it('keeps site chrome out of the root layout', () => {
    const rootLayout = read('layout.tsx');
    expect(rootLayout).not.toContain('SiteHeader');
    expect(rootLayout).not.toContain('SiteFooter');
  });

  it('renders site chrome for the storefront group', () => {
    const site = read(path.join('(site)', 'layout.tsx'));
    expect(site).toContain('SiteHeader');
    expect(site).toContain('SiteFooter');
    expect(site).toContain('skip-link');
  });

  it('leaves login and register in the auth group', () => {
    for (const route of ['login', 'register']) {
      expect(existsSync(path.join(app, '(auth)', route, 'page.tsx'))).toBe(true);
      expect(existsSync(path.join(app, '(site)', route))).toBe(false);
    }
  });
});

describe('navigation and headings', () => {
  const app = path.join(root, 'src', 'app');

  it('always offers a way back to the home page', async () => {
    const nav = await import('../src/components/layout/nav-links');
    const home = nav.NAV_LINKS.find((link) => link.href === '/');
    expect(home, 'the primary nav must contain a Home link').toBeDefined();
    expect(home?.label).toBe('Home');
  });

  it('renders every page with exactly one h1', () => {
    const pages: string[] = [];
    const walk = (dir: string) => {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (entry.name === 'api') continue;
          walk(full);
        } else if (entry.name === 'page.tsx' || entry.name === 'not-found.tsx') {
          pages.push(full);
        }
      }
    };
    walk(app);

    // A page may inherit its h1 from a layout (the admin shell renders the
    // page title), so a page only needs its own when no ancestor provides one.
    const layoutProvidesH1 = (file: string) => {
      let dir = path.dirname(file);
      while (dir.startsWith(app)) {
        const layout = path.join(dir, 'layout.tsx');
        if (existsSync(layout) && /<h1[\s>]/.test(readFileSync(layout, 'utf8'))) return true;
        dir = path.dirname(dir);
      }
      return false;
    };

    expect(pages.length).toBeGreaterThan(10);
    for (const page of pages) {
      const source = readFileSync(page, 'utf8');
      const hasH1 =
        /<h1[\s>]/.test(source) || /as="h1"/.test(source) || /as=\{['"]h1['"]\}/.test(source);
      expect(
        hasH1 || layoutProvidesH1(page),
        `${path.relative(app, page)} has no h1`,
      ).toBe(true);
    }
  });
});

describe('deployment config', () => {
  it('pins the Vercel framework preset so the build is not served as static output', () => {
    const config = JSON.parse(readFileSync(path.join(root, 'vercel.json'), 'utf8'));
    expect(config.framework).toBe('nextjs');
  });
});
