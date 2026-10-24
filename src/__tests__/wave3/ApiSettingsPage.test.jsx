import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ApiSettingsPage from '../../pages/ApiSettings';

const {
  getApiConfigMock,
  saveApiConfigMock,
  testGeminiApiMock,
  testDeepSeekApiMock,
  testOpenRouterApiMock,
  testStripeApiMock,
} = vi.hoisted(() => ({
  getApiConfigMock: vi.fn(),
  saveApiConfigMock: vi.fn(),
  testGeminiApiMock: vi.fn(),
  testDeepSeekApiMock: vi.fn(),
  testOpenRouterApiMock: vi.fn(),
  testStripeApiMock: vi.fn(),
}));

vi.mock('../../services/apiConfig', () => ({
  getApiConfig: getApiConfigMock,
  saveApiConfig: saveApiConfigMock,
  testGeminiApi: testGeminiApiMock,
  testDeepSeekApi: testDeepSeekApiMock,
  testOpenRouterApi: testOpenRouterApiMock,
  testStripeApi: testStripeApiMock,
}));

const freshConfig = () => ({
  gemini: { apiKey: '', enabled: false, lastTested: null, testStatus: null },
  deepseek: { apiKey: '', enabled: false, lastTested: null, testStatus: null },
  openrouter: { apiKey: '', enabled: false, lastTested: null, testStatus: null },
  stripe: { publishableKey: '', secretKey: '', enabled: false, lastTested: null, testStatus: null },
});

function renderApiSettings() {
  return render(
    <MemoryRouter>
      <ApiSettingsPage />
    </MemoryRouter>
  );
}

describe('ApiSettingsPage', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    getApiConfigMock.mockReturnValue(freshConfig());
    saveApiConfigMock.mockReturnValue(true);
  });

  it('renders the security notice and one settings card per provider', () => {
    renderApiSettings();

    expect(screen.getByRole('heading', { level: 1, name: 'API Configuration' })).toBeTruthy();
    expect(screen.getByText('Security Notice')).toBeTruthy();
    expect(screen.getByText(/stored in your browser's localStorage/)).toBeTruthy();

    ['Google Gemini', 'DeepSeek', 'OpenRouter', 'Stripe'].forEach((name) => {
      expect(screen.getByRole('heading', { name })).toBeTruthy();
    });
    expect(screen.getByLabelText('Gemini API Key')).toBeTruthy();
    expect(screen.getByLabelText('OpenRouter API Key')).toBeTruthy();
    expect(screen.getByLabelText('Publishable Key')).toBeTruthy();
    expect(screen.getByLabelText('Secret Key (optional, stored securely)')).toBeTruthy();
  });

  it('saves the edited keys and confirms with a transient Saved! state', async () => {
    renderApiSettings();

    fireEvent.change(screen.getByLabelText('Gemini API Key'), {
      target: { value: 'AIza-test-key' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save Configuration' }));

    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled();

    expect(
      await screen.findByRole('button', { name: 'Saved!' }, { timeout: 3000 })
    ).toBeTruthy();
    expect(saveApiConfigMock).toHaveBeenCalledTimes(1);
    expect(saveApiConfigMock).toHaveBeenCalledWith(
      expect.objectContaining({
        gemini: expect.objectContaining({ apiKey: 'AIza-test-key' }),
      })
    );
  });

  it('tests a provider connection and renders the reported model count', async () => {
    testGeminiApiMock.mockResolvedValue({
      success: true,
      message: 'Gemini API connection successful!',
      models: 42,
    });
    renderApiSettings();

    fireEvent.change(screen.getByLabelText('Gemini API Key'), {
      target: { value: 'AIza-test-key' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'Test Connection' })[0]);

    expect(await screen.findByText('Gemini API connection successful!')).toBeTruthy();
    expect(screen.getByText('42 models available')).toBeTruthy();
    expect(testGeminiApiMock).toHaveBeenCalledWith('AIza-test-key');
  });

  it('refuses to test Stripe without a publishable key', async () => {
    renderApiSettings();

    fireEvent.click(screen.getAllByRole('button', { name: 'Test Connection' })[3]);

    expect(await screen.findByText('Please enter publishable key first')).toBeTruthy();
    expect(testStripeApiMock).not.toHaveBeenCalled();
  });

  it('imports a JSON configuration and persists the merged keys', async () => {
    renderApiSettings();

    fireEvent.click(screen.getByRole('button', { name: 'Import Config' }));
    const importer = screen.getByPlaceholderText('Paste JSON configuration here...');
    fireEvent.change(importer, {
      target: { value: JSON.stringify({ gemini: { apiKey: 'imported-key' } }) },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Import Configuration' }));

    await waitFor(() =>
      expect(saveApiConfigMock).toHaveBeenCalledWith(
        expect.objectContaining({
          gemini: expect.objectContaining({ apiKey: 'imported-key' }),
          deepseek: expect.objectContaining({ apiKey: '' }),
        })
      )
    );
    expect(screen.queryByPlaceholderText('Paste JSON configuration here...')).toBeNull();
  });
});
