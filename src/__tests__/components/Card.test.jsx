import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Card, { CardContent, CardTitle } from '../../components/ui/Card';

describe('Card', () => {
  it('renders its content and forwards attributes', () => {
    render(
      <Card data-testid="card">
        <CardTitle>Account</CardTitle>
        <CardContent>Profile settings</CardContent>
      </Card>
    );

    expect(screen.getByTestId('card')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Account' })).toBeInTheDocument();
    expect(screen.getByText('Profile settings')).toBeInTheDocument();
  });

  it('supports keyboard activation when interactive', () => {
    const onClick = vi.fn();
    render(<Card onClick={onClick}>Open details</Card>);
    const card = screen.getByRole('button', { name: 'Open details' });

    fireEvent.keyDown(card, { key: 'Enter' });

    expect(onClick).toHaveBeenCalledOnce();
  });

  it('supports custom components without leaking motion props', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const CustomSection = ({ children, ...rest }) => <section {...rest}>{children}</section>;
    try {
      render(
        <Card as={CustomSection} hoverable>
          Custom details
        </Card>
      );
      const card = screen.getByText('Custom details').closest('section');

      expect(card).not.toBeNull();
      expect(card).not.toHaveAttribute('whilehover');
      expect(errorSpy.mock.calls.join('\n')).not.toContain('whileHover');
    } finally {
      errorSpy.mockRestore();
    }
  });

  it('keeps motion props off the rendered DOM element', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    try {
      render(<Card hoverable>Hover details</Card>);
      const card = screen.getByText('Hover details');

      expect(card).not.toHaveAttribute('whilehover');
      expect(errorSpy.mock.calls.join('\n')).not.toContain('whileHover');
    } finally {
      errorSpy.mockRestore();
    }
  });
});
