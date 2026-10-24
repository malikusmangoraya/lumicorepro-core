import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import Home from '../../pages/Home';

/**
 * The hero background lazily imports the three.js canvas; it carries no text or
 * behaviour this suite asserts on, so stub it out to keep the tests fast.
 */
vi.mock('@/components/motion/HeroCanvas', () => ({
  default: () => <div data-testid="hero-canvas" />,
}));

/**
 * CommandCenter probes the AI agent on mount. MSW is configured with
 * `onUnhandledRequest: 'error'`, so the API module must be mocked.
 */
vi.mock('@/services/api', () => ({
  aiAgentAPI: { checkHealth: vi.fn().mockResolvedValue({ status: 200 }) },
}));

const RouteEcho = () => {
  const location = useLocation();
  return <div data-testid="route-echo">{`${location.pathname}${location.search}`}</div>;
};

const renderHome = () =>
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/generate" element={<div>generate-page</div>} />
        <Route path="/templates" element={<div>templates-page</div>} />
        <Route path="/chat" element={<RouteEcho />} />
      </Routes>
    </MemoryRouter>
  );

describe('Home page', () => {
  it('renders the hero heading, badge, description and trust points', () => {
    renderHome();

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toContain('Build Any Website');
    expect(heading.textContent).toContain('With One Prompt');
    expect(screen.getByText(/60 Templates · 12 Industries/)).toBeTruthy();
    expect(screen.getByText(/most autonomous website generation agent/)).toBeTruthy();
    expect(screen.getByText('No credit card required')).toBeTruthy();
    expect(screen.getByText('Offline mode included')).toBeTruthy();
    expect(screen.getByText('Gemini · DeepSeek · OpenRouter')).toBeTruthy();
  });

  it('routes the primary hero CTA to the generator', () => {
    renderHome();

    fireEvent.click(screen.getByRole('button', { name: /^generate website free$/i }));

    expect(screen.getByText('generate-page')).toBeTruthy();
  });

  it('routes the secondary hero CTA and the showcase CTA to the template gallery', () => {
    const first = renderHome();

    // "Browse Templates" appears in the hero and in the closing CTA.
    fireEvent.click(screen.getAllByRole('button', { name: /^browse templates$/i })[0]);
    expect(screen.getByText('templates-page')).toBeTruthy();
    first.unmount();

    renderHome();
    fireEvent.click(screen.getByRole('button', { name: /view all 60 templates/i }));
    expect(screen.getByText('templates-page')).toBeTruthy();
  });

  it('renders every marketing section and all 15 pipeline phases', () => {
    renderHome();

    expect(
      screen.getByRole('heading', { level: 2, name: 'Every Industry. Market-Ready.' })
    ).toBeTruthy();
    expect(
      screen.getByRole('heading', { level: 2, name: 'Why LumicorePro is Unmatched' })
    ).toBeTruthy();
    expect(
      screen.getByRole('heading', { level: 2, name: '9-Phase Generation Pipeline' })
    ).toBeTruthy();
    expect(screen.getByRole('heading', { level: 2, name: 'Teams Ship Faster' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 3, name: '9-Phase AI Pipeline' })).toBeTruthy();
    expect(screen.getAllByText(/^(0[1-9]|1[0-5])$/)).toHaveLength(15);
    expect(screen.getByRole('heading', { level: 3, name: 'Market Analysis' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dashboard (5)' })).toBeTruthy();
  });

  it('drives the Command Center: health badge, suggestion fill and Enter-to-chat', async () => {
    renderHome();

    expect(await screen.findByText('Agent online')).toBeTruthy();

    const prompt = screen.getByRole('textbox');
    const send = screen.getByRole('button', { name: 'Send' });
    expect(send).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'E-commerce store' }));
    expect(prompt).toHaveValue(
      'Build a complete e-commerce store for a premium electronics brand with checkout'
    );
    expect(send).toBeEnabled();

    fireEvent.keyDown(prompt, { key: 'Enter' });

    const echo = screen.getByTestId('route-echo');
    expect(echo.textContent.startsWith('/chat?prompt=')).toBe(true);
    expect(decodeURIComponent(echo.textContent)).toContain(
      'Build a complete e-commerce store for a premium electronics brand with checkout'
    );
  });

  it('routes the closing CTA to the generator', () => {
    renderHome();

    fireEvent.click(screen.getByRole('button', { name: /start generating free/i }));

    expect(screen.getByText('generate-page')).toBeTruthy();
  });
});
