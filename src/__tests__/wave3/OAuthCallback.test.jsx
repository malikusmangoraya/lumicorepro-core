import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import OAuthCallbackPage from '../../pages/OAuthCallback';

const { appState } = vi.hoisted(() => ({
  appState: { login: vi.fn() },
}));

vi.mock('../../context/AppContext', () => ({ useAppContext: () => appState }));

const renderCallback = (query = '') =>
  render(
    <MemoryRouter initialEntries={[`/oauth/callback${query}`]}>
      <Routes>
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
        <Route path="/" element={<div>home-page</div>} />
        <Route path="/login" element={<div>login-page</div>} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('OAuthCallback page', () => {
  it('signs the user in with the callback token/user and redirects home', () => {
    const user = { id: 7, email: 'ada@example.com', name: 'Ada' };
    renderCallback(`?token=jwt-oauth&user=${encodeURIComponent(JSON.stringify(user))}`);

    expect(appState.login).toHaveBeenCalledWith(user, 'jwt-oauth');
    expect(screen.getByRole('heading', { level: 1, name: 'Signed in' })).toBeInTheDocument();
    expect(screen.getByText('Signed in successfully.')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1200);
    });
    expect(screen.getByText('home-page')).toBeInTheDocument();
  });

  it('renders a provider error and links back to sign in', () => {
    renderCallback('?error=access_denied');

    expect(
      screen.getByRole('heading', { level: 1, name: 'Authentication error' })
    ).toBeInTheDocument();
    expect(screen.getByText('access_denied')).toBeInTheDocument();
    expect(appState.login).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Go to Sign In' }));
    expect(screen.getByText('login-page')).toBeInTheDocument();
  });

  it('rejects a callback with no token or user data', () => {
    renderCallback();

    expect(screen.getByText(/missing required data/i)).toBeInTheDocument();
    expect(appState.login).not.toHaveBeenCalled();
  });

  it('rejects a callback whose user payload is not valid JSON', () => {
    renderCallback('?token=jwt-oauth&user=not-json');

    expect(screen.getByText(/missing required data/i)).toBeInTheDocument();
    expect(appState.login).not.toHaveBeenCalled();
  });
});
