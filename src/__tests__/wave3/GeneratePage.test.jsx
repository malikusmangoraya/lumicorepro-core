import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppContext } from '../../context/AppContext';
import GeneratePage from '../../pages/Generate';

const { generateMock } = vi.hoisted(() => ({ generateMock: vi.fn() }));

vi.mock('../../services/api', () => ({
  aiAgentAPI: {
    generate: generateMock,
    analyzeVision: vi.fn(),
    connectDomain: vi.fn(),
  },
  previewAPI: {
    create: vi.fn(),
    deploy: vi.fn(),
  },
  resolvePreviewUrl: (raw) => raw,
}));

const appContext = { language: 'en', user: null };

function renderGenerate() {
  return render(
    <MemoryRouter>
      <AppContext.Provider value={appContext}>
        <GeneratePage />
      </AppContext.Provider>
    </MemoryRouter>
  );
}

const getPromptBox = () => screen.getByLabelText('Website description prompt');
const getGenerateButton = () => screen.getByRole('button', { name: 'Generate website' });

describe('GeneratePage — prompt entry', () => {
  beforeEach(() => {
    generateMock.mockReset();
    localStorage.clear();
  });

  it('renders the header, prompt textarea and provider cards with Generate disabled', () => {
    renderGenerate();

    expect(screen.getByRole('heading', { level: 1, name: 'AI Website Generator' })).toBeTruthy();
    expect(getPromptBox()).toBeTruthy();
    expect(getPromptBox()).toHaveAttribute(
      'placeholder',
      expect.stringContaining('Build a restaurant website')
    );
    expect(getGenerateButton()).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Select Gemini 2.5 Flash' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    // Five provider options are offered.
    ['Gemini 2.5 Flash', 'DeepSeek Chat', 'Claude 3.5 Sonnet', 'Mistral Large', 'OpenRouter'].forEach(
      (name) => expect(screen.getByRole('button', { name: `Select ${name}` })).toBeTruthy()
    );
  });

  it('enables Generate only after a prompt is typed and clears it again', () => {
    renderGenerate();

    fireEvent.change(getPromptBox(), { target: { value: 'Build a SaaS landing page' } });

    expect(screen.getByText(/25 characters/)).toBeTruthy();
    expect(getGenerateButton()).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Clear prompt' }));

    expect(getPromptBox()).toHaveValue('');
    expect(getGenerateButton()).toBeDisabled();
  });

  it('fills the prompt from an example prompt button', () => {
    renderGenerate();

    fireEvent.click(
      screen.getByRole('button', {
        name: /Use example: Pakistani restaurant website with online ordering/,
      })
    );

    expect(getPromptBox()).toHaveValue(
      'Pakistani restaurant website with online ordering, menu categories, and delivery tracking'
    );
    expect(getGenerateButton()).toBeEnabled();
  });

  it('toggles the selected AI provider', () => {
    renderGenerate();

    const gemini = screen.getByRole('button', { name: 'Select Gemini 2.5 Flash' });
    const claude = screen.getByRole('button', { name: 'Select Claude 3.5 Sonnet' });

    fireEvent.click(claude);

    expect(claude).toHaveAttribute('aria-pressed', 'true');
    expect(gemini).toHaveAttribute('aria-pressed', 'false');
  });

  it('submits the prompt with the selected provider, language and region', async () => {
    generateMock.mockReturnValue(new Promise(() => {}));
    renderGenerate();

    fireEvent.change(getPromptBox(), { target: { value: 'Build an online bakery' } });
    fireEvent.click(screen.getByRole('button', { name: 'Select Claude 3.5 Sonnet' }));
    fireEvent.change(screen.getByLabelText('Output Language'), { target: { value: 'ur' } });
    fireEvent.change(screen.getByLabelText('Region / Compliance'), { target: { value: 'EU' } });

    fireEvent.click(getGenerateButton());

    await waitFor(() => expect(generateMock).toHaveBeenCalledTimes(1));
    expect(generateMock).toHaveBeenCalledWith({
      prompt: 'Build an online bakery',
      provider: 'claude',
      language: 'ur',
      region: 'EU',
      animation_intensity: 'high',
    });

    // The page enters its running state while the pipeline is in flight.
    expect(await screen.findByText('Pipeline Running…')).toBeTruthy();
    expect(screen.getByRole('heading', { name: /Pipeline Progress/ })).toBeTruthy();
    expect(getPromptBox()).toBeDisabled();
    expect(getGenerateButton()).toBeDisabled();
  });
});
