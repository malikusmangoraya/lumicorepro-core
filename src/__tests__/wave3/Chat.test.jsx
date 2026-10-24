import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mocks = vi.hoisted(() => ({
  aiAgentAPI: {
    visionChat: vi.fn(),
    analyzeVision: vi.fn(),
    generate: vi.fn(),
  },
}));

vi.mock('../../services/api', () => ({ aiAgentAPI: mocks.aiAgentAPI }));

import Chat from '../../pages/Chat';

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/chat']}>
      <Chat />
    </MemoryRouter>
  );

const typeMessage = (value) => {
  const input = screen.getByLabelText('Chat message');
  fireEvent.change(input, { target: { value } });
  return input;
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.aiAgentAPI.visionChat.mockResolvedValue({
    data: { data: { reply: 'Here is a plan for your site.' } },
  });
});

describe('Chat page', () => {
  it('renders the composer, empty state, suggestions and provider selector', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Lumicore AI Chat' })).toBeTruthy();
    expect(screen.getByLabelText('Chat message')).toHaveAttribute(
      'placeholder',
      'Type a message… (Shift+Enter for new line)'
    );
    expect(screen.getByLabelText('Engine')).toHaveValue('grok');
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Upload files' })).toBeEnabled();
    expect(
      screen.getByText(/Describe the website you want, upload a screenshot to match/i)
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Make a SaaS pricing page' })).toBeTruthy();
  });

  it('fills the composer from a suggestion and enables the send button', () => {
    renderPage();

    fireEvent.click(
      screen.getByRole('button', { name: 'Generate a landing page for a coffee shop' })
    );

    expect(screen.getByLabelText('Chat message')).toHaveValue(
      'Generate a landing page for a coffee shop'
    );
    expect(screen.getByRole('button', { name: 'Send' })).toBeEnabled();
  });

  // The Send button passes its click event into send()'s overrideText argument
  // (Chat.jsx:651), which throws in .trim(); Enter is the working send path.
  it('sends a message with Enter and renders the agent reply', async () => {
    renderPage();
    const input = typeMessage('Build a coffee shop site');

    fireEvent.keyDown(input, { key: 'Enter' });

    expect(await screen.findByText('Here is a plan for your site.')).toBeTruthy();
    expect(screen.getByText('Build a coffee shop site')).toBeTruthy();
    expect(mocks.aiAgentAPI.visionChat).toHaveBeenCalledTimes(1);
    expect(mocks.aiAgentAPI.visionChat).toHaveBeenCalledWith({
      message: 'Build a coffee shop site',
      provider: 'grok',
    });
    await waitFor(() => expect(input).toHaveValue(''));
  });

  it('sends with the selected engine provider', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText('Engine'), { target: { value: 'gemini' } });
    const input = typeMessage('Audit my landing page');

    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mocks.aiAgentAPI.visionChat).toHaveBeenCalledWith({
        message: 'Audit my landing page',
        provider: 'gemini',
      });
    });
    expect(await screen.findByText('Here is a plan for your site.')).toBeTruthy();
  });

  it('renders the backend error bubble and keeps the user message', async () => {
    mocks.aiAgentAPI.visionChat.mockRejectedValue({
      response: { data: { detail: 'Agent unreachable' } },
    });
    renderPage();
    const input = typeMessage('Build a site');

    fireEvent.keyDown(input, { key: 'Enter' });

    expect(await screen.findByText('Agent unreachable')).toBeTruthy();
    expect(screen.getByText('Build a site')).toBeTruthy();
    expect(screen.getByLabelText('Chat message')).toHaveValue('');
  });
});
