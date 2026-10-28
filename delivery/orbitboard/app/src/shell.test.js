import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('Orbitboard static showcase shell', () => {
  it('provides a mount point and descriptive metadata for the app', () => {
    const shellPath = new URL('../index.html', import.meta.url);

    expect(existsSync(shellPath)).toBe(true);
    const html = readFileSync(shellPath, 'utf8');
    expect(html).toContain('<div id="root"></div>');
    expect(html).toMatch(/<meta\s+name="description"/);
  });
});
