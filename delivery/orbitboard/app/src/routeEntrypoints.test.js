import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { writeRouteEntrypoints } from '../scripts/routeEntrypoints.js';

describe('writeRouteEntrypoints', () => {
  let outputDirectory;

  afterEach(async () => {
    if (outputDirectory) await rm(outputDirectory, { force: true, recursive: true });
    outputDirectory = undefined;
  });

  it('creates static entry files for nested routes that must survive a page refresh', async () => {
    outputDirectory = await mkdtemp(join(tmpdir(), 'orbitboard-routes-'));
    await writeFile(join(outputDirectory, 'index.html'), '<main>Orbitboard</main>');

    await writeRouteEntrypoints(outputDirectory);

    for (const route of ['login', 'register', 'reset-password', 'account', 'services']) {
      await expect(readFile(join(outputDirectory, route, 'index.html'), 'utf8'))
        .resolves.toBe('<main>Orbitboard</main>');
    }
    await expect(readFile(join(outputDirectory, '404.html'), 'utf8'))
      .resolves.toBe('<main>Orbitboard</main>');
  });
});
