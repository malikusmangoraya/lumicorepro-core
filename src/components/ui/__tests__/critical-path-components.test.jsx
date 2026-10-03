import React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import Tooltip from '../Tooltip';
import ButtonMotion from '../ButtonMotion';

const readComponent = (name) =>
  fs.readFileSync(path.resolve(process.cwd(), 'src', 'components', 'ui', name), 'utf8');

afterEach(() => {
  vi.useRealTimers();
});

describe('Tooltip', () => {
  it('does not render the tooltip until the open delay elapses', () => {
    vi.useFakeTimers();
    render(
      <Tooltip content="Delete">
        <button type="button">Trigger</button>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByRole('button').parentElement);
    expect(screen.queryByRole('tooltip')).toBeNull();

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.getByRole('tooltip')).toBeTruthy();
    expect(screen.getByRole('tooltip').textContent).toBe('Delete');
  });

  it('honours a custom delay', () => {
    vi.useFakeTimers();
    render(
      <Tooltip content="Later" delay={500}>
        <button type="button">Trigger</button>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByRole('button').parentElement);
    act(() => {
      vi.advanceTimersByTime(499);
    });
    expect(screen.queryByRole('tooltip')).toBeNull();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(screen.getByRole('tooltip')).toBeTruthy();
  });

  it('opens on keyboard focus and closes on blur', () => {
    vi.useFakeTimers();
    render(
      <Tooltip content="Keyboard">
        <button type="button">Trigger</button>
      </Tooltip>
    );

    const trigger = screen.getByRole('button');
    fireEvent.focus(trigger.parentElement);
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.getByRole('tooltip')).toBeTruthy();

    fireEvent.blur(trigger.parentElement);
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(screen.queryByRole('tooltip')).toBeNull();
  });

  it('renders immediately when controlled', () => {
    render(
      <Tooltip content="Controlled" open>
        <button type="button">Trigger</button>
      </Tooltip>
    );
    expect(screen.getByRole('tooltip').textContent).toBe('Controlled');
  });

  it('is actually visible when controlled open is true, not stuck at opacity-0', () => {
    const { rerender } = render(
      <Tooltip content="Controlled" open>
        <button type="button">Trigger</button>
      </Tooltip>
    );
    // Regression guard: the CSS port kept the fade in local state that only
    // show/hide ever set, so a parent-driven `open` stayed permanently
    // invisible even though the text was in the DOM.
    const inner = () => screen.getByRole('tooltip').firstElementChild;
    expect(inner().className).toContain('opacity-100');

    rerender(
      <Tooltip content="Controlled" open={false}>
        <button type="button">Trigger</button>
      </Tooltip>
    );
    expect(screen.queryByRole('tooltip')).toBeNull();

    rerender(
      <Tooltip content="Controlled" open>
        <button type="button">Trigger</button>
      </Tooltip>
    );
    expect(inner().className).toContain('opacity-100');
  });

  it('reports open state through onOpenChange', () => {
    vi.useFakeTimers();
    const onOpenChange = vi.fn();
    render(
      <Tooltip content="Callback" onOpenChange={onOpenChange}>
        <button type="button">Trigger</button>
      </Tooltip>
    );

    fireEvent.mouseEnter(screen.getByRole('button').parentElement);
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(onOpenChange).toHaveBeenCalledWith(true);

    fireEvent.mouseLeave(screen.getByRole('button').parentElement);
    expect(onOpenChange).toHaveBeenLastCalledWith(false);
  });

  // The whole reason Tooltip is CSS-animated: a framer-motion import here puts
  // ~35 KB gzip on the first-paint path via MainLayout -> GlassNavbar -> IconButton.
  it('does not pull framer-motion into the module graph', () => {
    expect(readComponent('Tooltip.jsx')).not.toMatch(
      /^\s*import .*from ['"]framer-motion['"]/m
    );
  });
});

describe('ButtonMotion', () => {
  it('renders its children inside a real button', () => {
    render(<ButtonMotion>Press me</ButtonMotion>);
    const button = screen.getByRole('button', { name: 'Press me' });
    expect(button).toBeTruthy();
  });

  it('drives the scale from CSS custom properties, not a JS animation lib', () => {
    const { container } = render(
      <ButtonMotion hoverScale={1.05} tapScale={0.9} hoverY={-2}>
        Press me
      </ButtonMotion>
    );
    const wrapper = container.firstChild;
    expect(wrapper.style.getPropertyValue('--bm-hover-scale')).toBe('1.05');
    expect(wrapper.style.getPropertyValue('--bm-tap-scale')).toBe('0.9');
    expect(wrapper.style.getPropertyValue('--bm-hover-y')).toBe('-2px');
    expect(wrapper.className).toContain('bm-motion');
  });

  it('forwards variant/size/click through to the inner button', () => {
    const onClick = vi.fn();
    render(
      <ButtonMotion variant="outline" size="sm" onClick={onClick}>
        Go
      </ButtonMotion>
    );
    const button = screen.getByRole('button', { name: 'Go' });
    expect(button.className).toContain('h-8');
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('keeps className on the wrapper and other props on the button', () => {
    const { container } = render(
      <ButtonMotion className="mt-4" aria-label="Labelled">
        Go
      </ButtonMotion>
    );
    expect(container.firstChild.className).toContain('mt-4');
    expect(screen.getByRole('button').getAttribute('aria-label')).toBe('Labelled');
  });

  it('does not pull framer-motion into the module graph', () => {
    expect(readComponent('ButtonMotion.jsx')).not.toMatch(
      /^\s*import .*from ['"]framer-motion['"]/m
    );
  });
});
