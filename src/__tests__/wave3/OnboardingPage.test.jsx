import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import OnboardingPage from '../../pages/Onboarding';

vi.mock('../../components/common/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'dark', isDark: true, setTheme: vi.fn(), toggleTheme: vi.fn() }),
}));

const getProgressFill = (container) => container.querySelector('.h-full.bg-primary');

function goToPreferences() {
  fireEvent.click(screen.getByRole('button', { name: /Next/ }));
  fireEvent.click(screen.getByRole('button', { name: /Next/ }));
}

describe('OnboardingPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  it('starts on the welcome step with the role choices and empty progress', () => {
    const { container } = render(<OnboardingPage />);

    expect(screen.getByRole('heading', { name: 'Welcome!' })).toBeTruthy();
    expect(screen.getByText('Select your role to get started.')).toBeTruthy();
    ['Admin', 'Developer', 'Designer', 'Other'].forEach((role) => {
      expect(screen.getByRole('radio', { name: role })).toBeTruthy();
    });
    expect(screen.getByRole('button', { name: /Next/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Back/ })).toBeNull();
    expect(getProgressFill(container).style.width).toBe('0%');
  });

  it('reveals a custom role field only when Other is selected', () => {
    render(<OnboardingPage />);

    expect(screen.queryByPlaceholderText('e.g. Product Manager')).toBeNull();

    fireEvent.click(screen.getByRole('radio', { name: 'Other' }));
    const customRole = screen.getByPlaceholderText('e.g. Product Manager');
    fireEvent.change(customRole, { target: { value: 'Product Manager' } });

    expect(customRole).toHaveValue('Product Manager');
    expect(screen.getByRole('radio', { name: 'Other' })).toBeChecked();

    fireEvent.click(screen.getByRole('radio', { name: 'Admin' }));
    expect(screen.queryByPlaceholderText('e.g. Product Manager')).toBeNull();
  });

  it('navigates forward and back across the three steps while advancing progress', () => {
    const { container } = render(<OnboardingPage />);

    fireEvent.click(screen.getByRole('button', { name: /Next/ }));

    expect(screen.getByRole('heading', { name: 'Team Setup' })).toBeTruthy();
    expect(screen.getByPlaceholderText('My Team')).toBeTruthy();
    expect(screen.getByPlaceholderText(/email1@example.com/)).toBeTruthy();
    expect(getProgressFill(container).style.width).toBe('50%');

    fireEvent.click(screen.getByRole('button', { name: /Back/ }));

    expect(screen.getByRole('heading', { name: 'Welcome!' })).toBeTruthy();
    expect(getProgressFill(container).style.width).toBe('0%');
  });

  it('applies theme and notification preferences on the final step', () => {
    const { container } = render(<OnboardingPage />);
    goToPreferences();

    expect(screen.getByRole('heading', { name: 'Preferences' })).toBeTruthy();
    expect(getProgressFill(container).style.width).toBe('100%');

    fireEvent.click(screen.getByRole('button', { name: 'Dark' }));
    expect(screen.getByRole('button', { name: 'Dark' }).className).toContain('bg-primary');
    expect(screen.getByRole('button', { name: 'System' }).className).not.toContain('bg-primary');

    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('persists completion and shows a submitting state when finish is clicked', () => {
    render(<OnboardingPage />);
    goToPreferences();
    vi.useFakeTimers();

    fireEvent.click(screen.getByRole('button', { name: /Complete/ }));

    expect(localStorage.getItem('onboarding_complete')).toBe('true');
    const completing = screen.getByRole('button', { name: /Complete/ });
    expect(completing).toBeDisabled();
    expect(completing.querySelector('.animate-spin')).not.toBeNull();
  });
});
