import { fileURLToPath } from 'node:url';
import { writeRouteEntrypoints } from './routeEntrypoints.js';

await writeRouteEntrypoints(fileURLToPath(new URL('../dist/', import.meta.url)));
