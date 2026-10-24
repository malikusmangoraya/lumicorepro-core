import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AuthLayout from '../layouts/AuthLayout';

vi.mock('../components/common/BrandLogo', () => ({
  default: () => <div aria-label="LumicorePro home">LumicorePro</div>,
}));

describe('AuthLayout', () => {
  it('renders a focused auth shell without marketing navigation or footer', () => {
    render(
      <MemoryRouter>
        <AuthLayout />
      </MemoryRouter>
    );

    expect(screen.getByRole('main', { name: 'Authentication' })).toBeTruthy();
    expect(screen.queryByLabelText('LumicorePro home')).toBeNull();
    expect(screen.queryByText('Freebuff')).toBeNull();
    expect(screen.queryByRole('navigation')).toBeNull();
    expect(screen.queryByRole('contentinfo')).toBeNull();
  });
});
