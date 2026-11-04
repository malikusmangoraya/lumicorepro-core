import test from 'node:test';
import assert from 'node:assert/strict';
import { formatCurrency, formatNumber, translate } from './i18n.js';

test('English and Urdu evaluation messages are available with safe fallback', () => {
  assert.match(translate('en', 'evaluationPricing'), /Checkout is not enabled/);
  assert.match(translate('ur', 'evaluationPricing'), /ادائیگی فعال نہیں/);
  assert.equal(translate('ur', 'unknown-message'), 'unknown-message');
});

test('locale formatters use locale-aware digits and currencies', () => {
  assert.equal(formatNumber(1234, 'en'), '1,234');
  assert.match(formatCurrency(19, 'USD', 'en'), /19\.00/);
  assert.match(formatCurrency(19, 'USD', 'ur'), /19/);
});
