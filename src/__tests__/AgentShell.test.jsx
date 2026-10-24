import React from 'react';
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppContext } from '../context/AppContext';
import ThemeProvider from '../components/common/ThemeProvider';
import { AgentShellFrame } from '../components/navigation/AgentShell';

const context = { theme: 'light', toggleTheme: () => {}, addNotification: () => {} };

if (!window.matchMedia) {
  window.matchMedia = () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} });
}

function renderShell() {
  return render(
    <MemoryRouter initialEntries={['/workspace']}>
      <AppContext.Provider value={context}>
        <ThemeProvider>
          <AgentShellFrame>
            <h1>Agent Control Center</h1>
          </AgentShellFrame>
        </ThemeProvider>
      </AppContext.Provider>
    </MemoryRouter>
  );
}

describe('Agent OS shell', () => {
  it('renders the launch loop and accessible primary navigation', () => {
    renderShell();

    expect(screen.getByRole('main', { name: /agent os main content/i })).toBeTruthy();
    expect(screen.getByText('Launch loop')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Agent Runs' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('button', { name: 'Open navigation' })).toBeTruthy();
  });

  it('opens and closes mobile navigation without changing the content', () => {
    renderShell();

    fireEvent.click(screen.getByRole('button', { name: 'Open navigation' }));
    expect(screen.getByRole('button', { name: 'Close navigation' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close navigation' }));
    expect(screen.getByRole('button', { name: 'Open navigation' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Agent Control Center' })).toBeTruthy();
  });
});
