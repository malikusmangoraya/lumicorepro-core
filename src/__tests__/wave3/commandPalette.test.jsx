import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CommandPalette from '../../components/advanced/CommandPalette';

let onClose;
let onExecute;

beforeEach(() => {
  onClose = vi.fn();
  onExecute = vi.fn();
  document.documentElement.classList.remove('dark');
});

afterEach(() => {
  document.documentElement.classList.remove('dark');
});

function renderPalette(isOpen = true) {
  return render(<CommandPalette isOpen={isOpen} onClose={onClose} onExecute={onExecute} />);
}

describe('CommandPalette', () => {
  it('renders nothing while closed', () => {
    renderPalette(false);

    expect(screen.queryByPlaceholderText('Type a command or search...')).not.toBeInTheDocument();
  });

  it('lists every command grouped by category', () => {
    renderPalette();

    expect(screen.getByPlaceholderText('Type a command or search...')).toBeInTheDocument();
    for (const category of ['Navigation', 'AI Actions', 'Appearance', 'Account']) {
      expect(screen.getByText(category)).toBeInTheDocument();
    }
    expect(screen.getByText('Generate New Website')).toBeInTheDocument();
    expect(screen.getByText('11 commands')).toBeInTheDocument();
  });

  it('filters on labels and keywords and shows an empty state', () => {
    renderPalette();
    const input = screen.getByPlaceholderText('Type a command or search...');

    fireEvent.change(input, { target: { value: 'dark' } });
    expect(screen.getByRole('button', { name: 'Switch to Dark Mode' })).toBeInTheDocument();
    expect(screen.queryByText('Switch to Light Mode')).not.toBeInTheDocument();
    expect(screen.getByText('1 command')).toBeInTheDocument();

    fireEvent.change(input, { target: { value: 'nothing-matches' } });
    expect(screen.getByText('No commands found')).toBeInTheDocument();
  });

  it('executes a clicked command, reports it, and closes', () => {
    renderPalette();

    fireEvent.change(screen.getByPlaceholderText('Type a command or search...'), {
      target: { value: 'dark' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Switch to Dark Mode' }));

    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(onExecute).toHaveBeenCalledWith(expect.objectContaining({ id: 'theme-dark' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('supports arrow-key navigation and Enter execution', () => {
    renderPalette();

    fireEvent.change(screen.getByPlaceholderText('Type a command or search...'), {
      target: { value: 'theme' },
    });
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'Enter' });

    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(onExecute).toHaveBeenCalledWith(expect.objectContaining({ id: 'theme-dark' }));
  });

  it('closes on Escape and on backdrop clicks', () => {
    renderPalette();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.click(document.querySelector('div.fixed.inset-0'));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
