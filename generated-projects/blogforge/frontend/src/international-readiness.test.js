import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const root = new URL('.', import.meta.url);
const read = (path) => readFile(new URL(path, root), 'utf8');

test('pricing clearly labels evaluation credits and avoids false payment claims', async () => {
  const source = await read('pages/Pricing.jsx');
  assert.match(source, /payment checkout is not enabled/);
  assert.match(source, /do not trigger payment/);
  assert.doesNotMatch(source, /≈ $0.03[08] per article/);
  assert.match(source, /evaluationPricing/);
});

test('auth routes omit marketing banner, navbar, and footer while public routes retain them', async () => {
  const source = await read('App.jsx');
  assert.match(source, /isAuthRoute/);
  assert.ok(source.includes('{!isAuthRoute && <GlassNavbar brand="BlogForge" />}'));
  assert.ok(source.includes('{!isAuthRoute && <ModernFooter brand="BlogForge" />}'));
  assert.ok(source.includes('{!isAuthRoute && <div role="status"'));
});

test('app exposes a skip link and evaluation status banner', async () => {
  const source = await read('App.jsx');
  assert.match(source, /skip-link/);
  assert.match(source, /role=\"status\"/);
  assert.match(source, /id=\"main-content\"/);
});

test('navigation includes labeled language controls and mobile control relationship', async () => {
  const source = await read('components/common/GlassNavbar.jsx');
  assert.match(source, /locale-select/);
  assert.match(source, /aria-controls=\"mobile-navigation\"/);
  assert.match(source, /setLocale/);
});

test('legal pages identify reference-deployment assumptions', async () => {
  const privacy = await read('pages/Privacy.jsx');
  const terms = await read('pages/Terms.jsx');
  assert.match(privacy, /reference deployment/);
  assert.match(terms, /operator of this instance/);
});
