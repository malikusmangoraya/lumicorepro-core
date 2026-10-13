import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const readProductFile = (product, file) => readFileSync(
  new URL(`./${product}/frontend/${file}`, import.meta.url),
  'utf8',
);

test('Apex home uses automotive brand copy and avoids unsupported proof claims', () => {
  const home = readProductFile('apex', 'src/pages/Home.jsx');
  assert.match(home, /APEX MOTOR COLLECTIVE/);
  assert.match(home, /vehicles inspected/);
  assert.match(home, /As featured in/);
});

test('Apex metadata describes the automotive collective', () => {
  const html = readProductFile('apex', 'index.html');
  assert.match(html, /<title>Apex Motor Collective/);
  assert.match(html, /Curated performance and collector cars/);
  assert.doesNotMatch(html, /Apex Digital|B2B teams/);
});

test('ClaimFlow metadata describes the claims workflow product', () => {
  const html = readProductFile('claimflow-ai', 'index.html');
  assert.match(html, /<title>ClaimFlow — Claims intake without the backlog/);
  assert.match(html, /Claims intake without the backlog/);
  assert.doesNotMatch(html, /fintech platform built for teams/);
});
