import { copyFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const STATIC_ROUTES = [
  'services',
  'about',
  'pricing',
  'contact',
  'privacy',
  'terms',
  'login',
  'register',
  'reset-password',
  'account',
  'admin',
  'checkout',
];

export async function writeRouteEntrypoints(outputDirectory) {
  const indexFile = join(outputDirectory, 'index.html');
  await copyFile(indexFile, join(outputDirectory, '404.html'));

  await Promise.all(STATIC_ROUTES.map(async (route) => {
    const routeDirectory = join(outputDirectory, route);
    await mkdir(routeDirectory, { recursive: true });
    await copyFile(indexFile, join(routeDirectory, 'index.html'));
  }));
}
