import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  exportApiConfig,
  getApiConfig,
  getApiKey,
  importApiConfig,
  isProviderEnabled,
  resetApiConfig,
  saveApiConfig,
  testDeepSeekApi,
  testGeminiApi,
  testOpenRouterApi,
  testStripeApi,
  updateProviderConfig,
} from '../../services/apiConfig';

const STORAGE_KEY = 'lumicorepro_api_config';

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('apiConfig — storage', () => {
  it('returns the full default configuration when nothing is stored', () => {
    const config = getApiConfig();

    expect(Object.keys(config)).toEqual(['gemini', 'deepseek', 'openrouter', 'stripe']);
    expect(config.gemini).toEqual({
      apiKey: '',
      enabled: false,
      lastTested: null,
      testStatus: null,
    });
    expect(config.stripe).toMatchObject({ publishableKey: '', secretKey: '', enabled: false });
  });

  it('reads a saved configuration back', () => {
    // getApiConfig() only shallow-copies: nested provider objects are shared with
    // the module defaults, so clone before editing (see bug note in the report).
    const config = JSON.parse(JSON.stringify(getApiConfig()));
    config.gemini.apiKey = 'gemini-key';
    config.gemini.enabled = true;
    expect(saveApiConfig(config)).toBe(true);

    const loaded = getApiConfig();
    expect(loaded.gemini).toMatchObject({ apiKey: 'gemini-key', enabled: true });
    expect(loaded.deepseek.enabled).toBe(false);
  });

  it('merges stored top-level providers over the defaults', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ openrouter: { apiKey: 'or-key' } }));

    const config = getApiConfig();
    expect(config.openrouter.apiKey).toBe('or-key');
    expect(config.gemini.apiKey).toBe('');
    expect(config.stripe.enabled).toBe(false);
  });

  it('falls back to defaults when the stored JSON is corrupt', () => {
    localStorage.setItem(STORAGE_KEY, '{not-json');

    expect(getApiConfig().gemini.apiKey).toBe('');
    expect(getApiConfig().stripe.publishableKey).toBe('');
  });

  it('updates a provider config and rejects unknown providers', () => {
    expect(updateProviderConfig('deepseek', { apiKey: 'ds-key', enabled: true })).toBe(true);
    expect(getApiConfig().deepseek).toMatchObject({ apiKey: 'ds-key', enabled: true });

    expect(updateProviderConfig('nope', { apiKey: 'x' })).toBe(false);
  });

  it('resets the stored configuration', () => {
    updateProviderConfig('gemini', { apiKey: 'key' });
    expect(localStorage.getItem(STORAGE_KEY)).toBeTruthy();

    expect(resetApiConfig()).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    expect(getApiConfig().gemini.apiKey).toBe('');
  });

  it('exports pretty JSON and imports it back, rejecting invalid JSON', () => {
    updateProviderConfig('stripe', { publishableKey: 'pk_test_123' });
    const exported = exportApiConfig();
    expect(exported).toContain('\n  "stripe"');

    resetApiConfig();
    expect(importApiConfig(exported)).toBe(true);
    expect(getApiConfig().stripe.publishableKey).toBe('pk_test_123');

    expect(importApiConfig('{broken')).toBe(false);
  });
});

describe('apiConfig — key lookup and enable flags', () => {
  it('returns provider keys and null for unknown providers', () => {
    updateProviderConfig('gemini', { apiKey: 'gemini-key' });
    updateProviderConfig('stripe', { publishableKey: 'pk_test_abc', secretKey: 'sk_test_abc' });

    expect(getApiKey('gemini')).toBe('gemini-key');
    expect(getApiKey('stripe')).toBe('pk_test_abc');
    expect(getApiKey('unknown')).toBeNull();
    expect(getApiKey('openrouter')).toBeNull();
  });

  it('falls back to the Stripe secret key when no publishable key exists', () => {
    updateProviderConfig('stripe', { publishableKey: '', secretKey: 'sk_test_secret' });

    expect(getApiKey('stripe')).toBe('sk_test_secret');
  });

  it('reports enabled state from the presence of a key', () => {
    expect(isProviderEnabled('gemini')).toBe(false);

    updateProviderConfig('gemini', { apiKey: 'k' });
    expect(isProviderEnabled('gemini')).toBe(true);

    updateProviderConfig('stripe', { secretKey: 'sk_test_x' });
    expect(isProviderEnabled('stripe')).toBe(true);
    expect(isProviderEnabled('openrouter')).toBe(false);
    expect(isProviderEnabled('nope')).toBe(false);
  });
});

describe('apiConfig — connectivity tests', () => {
  it('validates the Stripe key format without network access', async () => {
    await expect(testStripeApi('bad-key')).resolves.toEqual({
      success: false,
      message: 'Invalid Stripe publishable key format',
    });
    await expect(testStripeApi('pk_test_123')).resolves.toEqual({
      success: true,
      message: 'Stripe key format is valid! (Full test requires backend)',
      isTestKey: true,
    });
    await expect(testStripeApi('pk_live_123')).resolves.toMatchObject({
      success: true,
      isTestKey: false,
    });
  });

  it('tests the Gemini API and returns the model count', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ models: [{ name: 'a' }, { name: 'b' }] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(testGeminiApi('gem-key')).resolves.toEqual({
      success: true,
      message: 'Gemini API connection successful!',
      models: 2,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      'https://generativelanguage.googleapis.com/v1beta/models?key=gem-key',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('surfaces the Gemini provider error and connection failures', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: { message: 'Bad key' } }) })
    );
    await expect(testGeminiApi('bad')).resolves.toEqual({ success: false, message: 'Bad key' });

    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    await expect(testGeminiApi('bad')).resolves.toEqual({
      success: false,
      message: 'Connection failed: offline',
    });
  });

  it('tests DeepSeek and maps its data array', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: [{ id: 'deepseek-chat' }] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(testDeepSeekApi('ds-key')).resolves.toEqual({
      success: true,
      message: 'DeepSeek API connection successful!',
      models: 1,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.deepseek.com/v1/models',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer ds-key' }),
      })
    );
  });

  it('tests OpenRouter and reports failures', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: { label: 'My key' } }) })
    );
    await expect(testOpenRouterApi('or-key')).resolves.toEqual({
      success: true,
      message: 'OpenRouter API connection successful!',
      keyInfo: 'My key',
    });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) }));
    await expect(testOpenRouterApi('bad')).resolves.toEqual({
      success: false,
      message: 'Invalid API key or unauthorized',
    });
  });
});
