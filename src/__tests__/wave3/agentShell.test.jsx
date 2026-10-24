import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const themeState = vi.hoisted(() => ({ isDark: true, toggleTheme: vi.fn() }));

vi.mock('../../components/common/ThemeProvider', () => ({
  useTheme: () => themeState,
}));

vi.mock('../../components/common/BrandLogo', () => ({
  default: () => <div data-testid="brand-logo" />,
}));

import { AgentShellFrame } from '../../components/navigation/AgentShell';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

function renderShell(route = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AgentShellFrame>
        <p>Workspace content</p>
      </AgentShellFrame>
      <LocationProbe />
    </MemoryRouter>
  );
}

beforeEach(() => {
  themeState.isDark = true;
  themeState.toggleTheme.mockReset();
});

describe('AgentShellFrame', () => {
  it('renders the full rail, the current section, and the page content', () => {
    renderShell('/dashboard');

    const rail = screen.getByRole('complementary', { name: 'Agent OS navigation' });
    expect(within(rail).getByRole('button', { name: 'Overview' })).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(within(rail).getByRole('button', { name: 'Generate' })).not.toHaveAttribute(
      'aria-current'
    );
    expect(within(rail).getByRole('button', { name: 'Billing' })).toBeInTheDocument();
    expect(screen.getByText('Workspace content')).toBeInTheDocument();
    expect(screen.getByRole('main', { name: 'Agent OS main content' })).toBeInTheDocument();
  });

  it('marks nested routes active and navigates when a rail item is clicked', () => {
    renderShell('/workspace/run-42');

    const rail = screen.getByRole('complementary', { name: 'Agent OS navigation' });
    expect(within(rail).getByRole('button', { name: 'Agent Runs' })).toHaveAttribute(
      'aria-current',
      'page'
    );

    fireEvent.click(within(rail).getByRole('button', { name: 'Billing' }));
    expect(screen.getByTestId('location')).toHaveTextContent('/billing');
  });

  it('renders the seven launch-loop phases with the workspace phase current', () => {
    renderShell('/workspace');

    for (const phase of ['Brief', 'Strategy', 'Design', 'Build', 'Critique', 'Proof', 'Ship']) {
      expect(screen.getByText(phase)).toBeInTheDocument();
    }
    // '/workspace' maps to phase index 5 (Proof).
    expect(screen.getByText('Proof')).toHaveClass('text-foreground');
    expect(screen.getByText('Brief')).toHaveClass('text-muted-foreground');
  });

  it('toggles the theme from the header', () => {
    renderShell();

    fireEvent.click(screen.getByRole('button', { name: 'Use light theme' }));
    expect(themeState.toggleTheme).toHaveBeenCalledTimes(1);

    themeState.isDark = false;
    renderShell();
    expect(screen.getByRole('button', { name: 'Use dark theme' })).toBeInTheDocument();
  });

  it('opens and closes the mobile navigation drawer', () => {
    renderShell();

    fireEvent.click(screen.getByRole('button', { name: 'Open navigation' }));
    const overlay = screen.getByRole('button', { name: 'Close navigation overlay' });
    expect(overlay).toBeInTheDocument();

    fireEvent.click(overlay);
    expect(
      screen.queryByRole('button', { name: 'Close navigation overlay' })
    ).not.toBeInTheDocument();
  });

  it('collapses the rail into icon-only mode', () => {
    renderShell();

    expect(screen.getByText('Launch readiness')).toBeInTheDocument();
    expect(screen.getByText('Free workspace')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Toggle navigation rail' }));

    expect(screen.queryByText('Launch readiness')).not.toBeInTheDocument();
    expect(screen.queryByText('Free workspace')).not.toBeInTheDocument();
  });

  it('broadcasts Ctrl+K from the command palette button', () => {
    renderShell();
    const listener = vi.fn();
    window.addEventListener('keydown', listener);

    const button = screen.getByRole('button', { name: 'Open command palette' });
    fireEvent.click(button);

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0][0]).toMatchObject({ key: 'k', ctrlKey: true });
    window.removeEventListener('keydown', listener);
  });
});
