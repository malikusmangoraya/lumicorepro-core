import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// Finding: lucide-react 1.48 no longer exports the brand icons Chrome, Github
// or Facebook, so `src/components/auth/SocialLogin.jsx:2` imports undefined
// components and the real module throws on render. Stub them here so the
// provider logic itself can be exercised independently of that bug.
vi.mock('lucide-react', async (importOriginal) => {
  const actual = await importOriginal();
  const StubIcon = (props) => <svg aria-hidden="true" {...props} />;
  return {
    ...actual,
    Chrome: actual.Chrome ?? StubIcon,
    Github: actual.Github ?? StubIcon,
    Facebook: actual.Facebook ?? StubIcon,
  };
});

import SocialLogin from '../../components/auth/SocialLogin';

const PROVIDERS = [
  { id: 'google', label: 'Google' },
  { id: 'github', label: 'GitHub' },
  { id: 'facebook', label: 'Facebook' },
];

describe('SocialLogin', () => {
  it('renders one accessible button per provider', () => {
    render(<SocialLogin />);

    expect(screen.getByText('Or continue with')).toBeInTheDocument();
    PROVIDERS.forEach(({ label }) => {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    });
  });

  it('reports the provider id when a button is clicked', () => {
    const onProviderClick = vi.fn();
    render(<SocialLogin onProviderClick={onProviderClick} />);

    PROVIDERS.forEach(({ id, label }, index) => {
      fireEvent.click(screen.getByRole('button', { name: label }));
      expect(onProviderClick).toHaveBeenNthCalledWith(index + 1, id);
    });
    expect(onProviderClick).toHaveBeenCalledTimes(3);
  });

  it('does not throw when no handler is supplied', () => {
    render(<SocialLogin />);

    expect(() => fireEvent.click(screen.getByRole('button', { name: 'Google' }))).not.toThrow();
  });

  it('shows a spinner on the busy provider and disables the others', () => {
    render(<SocialLogin loadingProvider="github" />);

    const github = screen.getByRole('button', { name: /GitHub/ });
    expect(within(github).getByRole('status')).toBeInTheDocument();
    // Finding: the busy provider itself is not disabled, so it can be clicked again.
    expect(github).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Google' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Facebook' })).toBeDisabled();
  });

  it('accepts a custom section title', () => {
    render(<SocialLogin title="Sign in with" />);

    expect(screen.getByText('Sign in with')).toBeInTheDocument();
  });
});
