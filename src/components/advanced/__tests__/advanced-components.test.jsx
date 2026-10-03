import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import GlassCard from '../GlassCard';
import FluidButton from '../FluidButton';
import AnimatedBackground from '../AnimatedBackground';
import CommandPalette from '../CommandPalette';
import AIChat from '../AIChat';

// Mock canvas getContext for AnimatedBackground in jsdom
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  beginPath: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  fillRect: vi.fn(),
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
}));

describe('GlassCard Component', () => {
  it('renders children properly', () => {
    render(<GlassCard><div>Card Content</div></GlassCard>);
    expect(screen.getByText('Card Content')).toBeTruthy();
  });

  it('applies correct intensity classes', () => {
    const { container, rerender } = render(
      <GlassCard intensity="low">Low Intensity</GlassCard>
    );
    expect(container.firstChild.className).toContain('backdrop-blur-sm');

    rerender(<GlassCard intensity="ultra">Ultra Intensity</GlassCard>);
    expect(container.firstChild.className).toContain('backdrop-blur-xl');
  });

  it('supports custom borderRadius and onClick', () => {
    const handleClick = vi.fn();
    const { container } = render(
      <GlassCard borderRadius="2xl" onClick={handleClick}>Clickable Card</GlassCard>
    );
    expect(container.firstChild.className).toContain('rounded-2xl');
    fireEvent.click(container.firstChild);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe('FluidButton Component', () => {
  it('renders button label and fires onClick', () => {
    const handleClick = vi.fn();
    render(<FluidButton onClick={handleClick}>Click Me</FluidButton>);
    const button = screen.getByRole('button', { name: /Click Me/i });
    expect(button).toBeTruthy();
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders loading state and prevents click', () => {
    const handleClick = vi.fn();
    render(<FluidButton loading onClick={handleClick}>Submit</FluidButton>);
    expect(screen.getByText(/Loading.../i)).toBeTruthy();
    const button = screen.getByRole('button');
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('supports disabled state', () => {
    render(<FluidButton disabled>Disabled Action</FluidButton>);
    const button = screen.getByRole('button', { name: /Disabled Action/i });
    expect(button.disabled).toBe(true);
  });
});

describe('AnimatedBackground Component', () => {
  it('renders canvas element without throwing', () => {
    const { container } = render(<AnimatedBackground theme="aurora" particleCount={20} />);
    const canvas = container.querySelector('canvas');
    expect(canvas).toBeTruthy();
  });
});

describe('CommandPalette Component', () => {
  it('renders commands when open', () => {
    const handleClose = vi.fn();
    render(<CommandPalette isOpen={true} onClose={handleClose} />);
    expect(screen.getByPlaceholderText(/Type a command or search.../i)).toBeTruthy();
    expect(screen.getByText('Go to Home')).toBeTruthy();
  });

  it('filters commands on search query', () => {
    render(<CommandPalette isOpen={true} onClose={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Type a command or search.../i);
    fireEvent.change(input, { target: { value: 'Dark Mode' } });
    expect(screen.getByText('Switch to Dark Mode')).toBeTruthy();
    expect(screen.queryByText('Go to Home')).toBeNull();
  });
});

describe('AIChat Component', () => {
  it('renders header, quick prompts and input textarea', () => {
    render(<AIChat />);
    expect(screen.getByText('AI Assistant')).toBeTruthy();
    expect(screen.getByText('Explain code')).toBeTruthy();
    expect(screen.getByPlaceholderText(/Ask anything.../i)).toBeTruthy();
  });

  it('fills input when quick prompt is clicked', () => {
    render(<AIChat />);
    const promptBtn = screen.getByText('Explain code');
    fireEvent.click(promptBtn);
    const textarea = screen.getByPlaceholderText(/Ask anything.../i);
    expect(textarea.value).toContain('explain how this code works');
  });
});
