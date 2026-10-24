import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mocks = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

vi.mock('../../services/api', () => ({ default: mocks.api }));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, name: 'Ada Lovelace' } }),
}));

// The particle canvas has no 2D context in jsdom; the decoration is not part
// of the behaviour under test.
vi.mock('../../components/advanced/AnimatedBackground', () => ({
  default: () => null,
}));

import AIDashboard from '../../pages/AIDashboard';

const projects = [
  { id: 1, name: 'Aurora Launchpad', created_at: '2026-10-01' },
  { id: 2, name: 'Bakery Storefront', created_at: '2026-09-28' },
];

const analytics = {
  total_projects: 12,
  total_generations: 240,
  avg_security_score: 91,
  avg_performance: 88,
};

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/ai-dashboard']}>
      <AIDashboard />
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  mocks.api.get.mockImplementation((url) => {
    if (url === '/ai/projects') return Promise.resolve({ data: { data: projects } });
    if (url === '/ai/analytics') return Promise.resolve({ data: { data: analytics } });
    return Promise.resolve({ data: { data: [] } });
  });
  mocks.api.post.mockResolvedValue({ data: { data: {} } });
});

describe('AIDashboard page', () => {
  it('renders usage statistics and recent projects from the API', async () => {
    renderPage();

    expect(
      screen.getByRole('heading', { level: 1, name: /AI Control Center/i })
    ).toBeTruthy();
    expect(screen.getByText('Projects Generated')).toBeTruthy();
    expect(screen.getByText('AI Generations')).toBeTruthy();
    expect(screen.getByText('Security Score')).toBeTruthy();
    expect(screen.getByText('Performance')).toBeTruthy();

    expect(await screen.findByText('Aurora Launchpad')).toBeTruthy();
    expect(screen.getByText('Bakery Storefront')).toBeTruthy();
    expect(await screen.findByText('240')).toBeTruthy();
    expect(screen.getByText('91')).toBeTruthy();
    expect(screen.getByText('88')).toBeTruthy();
    expect(screen.getByRole('button', { name: /View All Projects/i })).toBeTruthy();
  });

  it('keeps the dashboard usable when both requests return empty payloads', async () => {
    mocks.api.get.mockResolvedValue({ data: { data: [] } });

    renderPage();
    await waitFor(() => {
      expect(mocks.api.get).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByRole('heading', { name: 'Recent Projects' })).toBeTruthy();
    expect(screen.queryByText('Aurora Launchpad')).toBeNull();
    expect(screen.getByRole('button', { name: /View All Projects/i })).toBeTruthy();
  });

  it('rejects an empty prompt instead of starting a generation', async () => {
    renderPage();
    await screen.findByText('Aurora Launchpad');

    fireEvent.click(screen.getByRole('button', { name: /Generate Website/i }));

    expect(
      await screen.findByText('Please enter a description for your website.')
    ).toBeTruthy();
    expect(mocks.api.post).not.toHaveBeenCalled();
  });

  it('renders the shell when the dashboard requests fail', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    mocks.api.get.mockRejectedValue(new Error('network down'));

    renderPage();
    await waitFor(() => {
      expect(mocks.api.get).toHaveBeenCalledTimes(2);
    });

    expect(
      screen.getByRole('heading', { level: 1, name: /AI Control Center/i })
    ).toBeTruthy();
    expect(screen.getByText('Security Score')).toBeTruthy();
    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
