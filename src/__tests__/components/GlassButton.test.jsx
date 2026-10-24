import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ShoppingCart, Star } from 'lucide-react';
import GlassButton from '../../components/ui/GlassButton';

/**
 * Regression: lucide icons are forwardRef component objects, not plain
 * functions. GlassButton used to fall through its `typeof Icon === 'function'`
 * check and render the component object as a React child, throwing
 * "Objects are not valid as a React child" and white-screening any page that
 * passed rightIcon/leftIcon (e.g. the ProductListing template).
 */
describe('GlassButton icon rendering', () => {
  it('renders a forwardRef icon component instead of throwing', () => {
    render(
      <GlassButton rightIcon={ShoppingCart} leftIcon={Star}>
        Add
      </GlassButton>
    );
    expect(screen.getByRole('button', { name: /add/i })).toBeTruthy();
  });

  it('renders without icons', () => {
    render(<GlassButton>Plain</GlassButton>);
    expect(screen.getByRole('button', { name: /plain/i })).toBeTruthy();
  });

  it('renders a ready-made element icon unchanged', () => {
    render(<GlassButton rightIcon={<Star data-testid="star-icon" />}>Starred</GlassButton>);
    expect(screen.getByTestId('star-icon')).toBeTruthy();
  });
});
