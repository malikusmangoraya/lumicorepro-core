import { test } from 'node:test';
import assert from 'node:assert';
import { sanitizeHtml } from './components/generator/sanitize.js';

test('sanitize removes scripts, inline handlers, and javascript URLs', () => {
  const dirty = '<p onclick="alert(1)">Hi<script>alert(2)</script></p><a href="javascript:alert(3)">x</a><iframe src="https://evil"></iframe>';
  const clean = sanitizeHtml(dirty);
  assert.ok(!/<script/i.test(clean), 'no script tags');
  assert.ok(!/onclick=/i.test(clean), 'no inline handlers');
  assert.ok(!/javascript:/i.test(clean), 'no javascript: urls');
  assert.ok(!/<iframe/i.test(clean), 'no iframes');
  assert.ok(clean.includes('Hi'), 'keeps text content');
});
