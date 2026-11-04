import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const homeSource = await readFile(new URL('./pages/Home.jsx', import.meta.url), 'utf8');

test('landing page explains value, workflow, product features, audiences, and pricing path', () => {
  for (const phrase of [
    'A better way to',
    'publish consistently.',
    'One article, from brief to publish-ready',
    'Built for the whole workflow',
    'A practical writing partner for every team',
    'Questions, answered',
  ]) {
    assert.ok(homeSource.includes(phrase), `Expected landing page section: ${phrase}`);
  }
});
