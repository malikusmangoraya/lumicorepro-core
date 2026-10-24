import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

/**
 * Framer Motion is stubbed with plain DOM tags. Under jsdom its render loop
 * throws when BorderBeam's background value is not valid CSS, which makes the
 * suite nondeterministic; the wrappers under test are structural. Motion
 * behaviour itself is covered by the E2E suite.
 */
vi.mock('framer-motion', async () => {
  const React = await import('react');
  const makeMotion = (tag) =>
    React.forwardRef((props, ref) => {
      const {
        children,
        animate,
        initial,
        exit,
        transition,
        whileInView,
        viewport,
        variants,
        ...rest
      } = props;
      return React.createElement(tag, { ref, ...rest }, children);
    });
  // Cache per tag: a fresh component type per render would remount the node.
  const cache = new Map();
  return {
    motion: new Proxy(
      {},
      {
        get: (_target, tag) => {
          if (typeof tag !== 'string') return undefined;
          if (!cache.has(tag)) cache.set(tag, makeMotion(tag));
          return cache.get(tag);
        },
      }
    ),
    AnimatePresence: ({ children }) => children,
    useReducedMotion: () => false,
  };
});

import Reveal from '../../components/motion/Reveal';
import { StaggerContainer, StaggerItem } from '../../components/motion/StaggerGroup';
import BentoGrid from '../../components/motion/BentoGrid';
import BorderBeam from '../../components/motion/BorderBeam';
import HolographicCard from '../../components/motion/HolographicCard';
import MagneticButton from '../../components/motion/MagneticButton';
import SpotlightGrid from '../../components/motion/SpotlightGrid';
import TextMorph from '../../components/motion/TextMorph';

/**
 * SpotlightGrid.jsx:26 removes a listener with the undefined `handleMousePos`
 * instead of the handler it registered, so unmount throws a ReferenceError and
 * leaks the listener. Shim the free identifier so cleanup can run; the bug is
 * reported rather than patched in src/.
 */
beforeAll(() => {
  globalThis.handleMousePos = () => {};
});

afterAll(() => {
  delete globalThis.handleMousePos;
});

describe('Reveal', () => {
  it('renders its children and forwards className and DOM props', () => {
    render(
      <Reveal className="reveal-card" delay={0.2} data-testid="reveal">
        <p>Animated content</p>
      </Reveal>
    );

    const node = screen.getByTestId('reveal');
    expect(screen.getByText('Animated content')).toBeInTheDocument();
    expect(node).toHaveClass('reveal-card');
  });

  it('supports every direction without crashing', () => {
    for (const direction of ['up', 'down', 'left', 'right', 'none', 'unknown']) {
      const { unmount } = render(
        <Reveal direction={direction}>{`Copy ${direction}`}</Reveal>
      );
      expect(screen.getByText(`Copy ${direction}`)).toBeInTheDocument();
      unmount();
    }
  });
});

describe('StaggerGroup', () => {
  it('renders a staggered container with its items', () => {
    render(
      <StaggerContainer className="stagger-list" data-testid="stagger">
        <StaggerItem>First</StaggerItem>
        <StaggerItem className="second">Second</StaggerItem>
      </StaggerContainer>
    );

    expect(screen.getByTestId('stagger')).toHaveClass('stagger-list');
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toHaveClass('second');
  });
});

describe('BentoGrid', () => {
  it('renders children in an animated grid with the base column count', () => {
    const { container } = render(
      <BentoGrid className="bento">
        <div>Tile one</div>
        <div>Tile two</div>
      </BentoGrid>
    );

    const grid = container.firstElementChild;
    expect(grid).toHaveClass('bento', 'grid');
    expect(grid.style.gridTemplateColumns).toBe('repeat(1, 1fr)');
    expect(screen.getByText('Tile one')).toBeInTheDocument();
    expect(screen.getByText('Tile two')).toBeInTheDocument();
  });

  it('exposes BentoGrid.Item with span styles and extra props', () => {
    render(
      <BentoGrid>
        <BentoGrid.Item span={{ colSpan: 2, rowSpan: 3 }} className="wide" id="item">
          Wide tile
        </BentoGrid.Item>
      </BentoGrid>
    );

    const item = screen.getByText('Wide tile').closest('#item');
    expect(item).toHaveClass('wide');
    expect(item.style.gridColumn).toBe('span 2');
    expect(item.style.gridRow).toBe('span 3');
  });
});

describe('BorderBeam', () => {
  it('renders the beam layer and its content', () => {
    const { container } = render(
      <BorderBeam className="beam" color="from-pink-500 to-orange-500">
        Beam content
      </BorderBeam>
    );

    expect(container.firstElementChild).toHaveClass('relative', 'beam');
    expect(screen.getByText('Beam content')).toBeInTheDocument();
    const beam = container.querySelector('.absolute.inset-0');
    // jsdom drops the invalid `linear-gradient(... from-pink-500 ...)` value;
    // see BorderBeam.jsx:17 — Tailwind class names are not CSS colours.
    expect(beam.style.border).toBe('2px solid transparent');
    expect(beam.style.maskComposite).toBe('exclude');
  });
});

describe('HolographicCard', () => {
  it('reacts to pointer movement with glare and tilt state', () => {
    render(
      <HolographicCard data-testid="holo" glareOpacity={0.5}>
        Holo content
      </HolographicCard>
    );

    const card = screen.getByTestId('holo');
    card.getBoundingClientRect = () => ({
      left: 0,
      top: 0,
      width: 200,
      height: 100,
      right: 200,
      bottom: 100,
      x: 0,
      y: 0,
      toJSON: () => {},
    });

    const sheen = card.querySelector('[aria-hidden="true"]');
    expect(sheen.style.opacity).toBe('0');

    fireEvent.mouseOver(card);
    expect(sheen.style.opacity).toBe('0.5');

    fireEvent.mouseMove(card, { clientX: 150, clientY: 25 });
    expect(sheen.style.backgroundPosition).toBe('75% 25%');

    fireEvent.mouseOut(card);
    expect(sheen.style.opacity).toBe('0');
  });

  it('renders children with the base card classes', () => {
    render(
      <HolographicCard className="custom-holo">
        <h3>Inside</h3>
      </HolographicCard>
    );

    expect(screen.getByRole('heading', { name: 'Inside' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Inside' }).closest('.custom-holo')).not.toBeNull();
  });
});

const Icon = ({ className }) => <svg data-testid="cta-icon" className={className} />;

describe('MagneticButton', () => {
  it('renders label and both icon slots and calls onClick', () => {
    const onClick = vi.fn();
    render(
      <MagneticButton onClick={onClick} leftIcon={Icon} rightIcon={Icon} variant="glow">
        Magnetic
      </MagneticButton>
    );

    expect(screen.getAllByTestId('cta-icon')).toHaveLength(2);
    fireEvent.click(screen.getByRole('button', { name: 'Magnetic' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('applies size/variant classes and respects disabled', () => {
    render(
      <MagneticButton size="lg" variant="outline" disabled>
        Disabled
      </MagneticButton>
    );

    const button = screen.getByRole('button', { name: 'Disabled' });
    expect(button).toBeDisabled();
    expect(button.className).toContain('px-7');
    expect(button.className).toContain('border-border');
  });

  it('handles pointer movement within a measured button', () => {
    render(<MagneticButton>Move me</MagneticButton>);
    const button = screen.getByRole('button', { name: 'Move me' });
    button.getBoundingClientRect = () => ({
      left: 10,
      top: 20,
      width: 100,
      height: 40,
      right: 110,
      bottom: 60,
      x: 10,
      y: 20,
      toJSON: () => {},
    });

    fireEvent.mouseMove(button, { clientX: 60, clientY: 40 });
    fireEvent.mouseLeave(button);
    expect(button).toBeInTheDocument();
  });
});

describe('SpotlightGrid', () => {
  it('tracks pointer events and documents the mismatched cleanup handler', () => {
    const addSpy = vi.spyOn(Element.prototype, 'addEventListener');
    const removeSpy = vi.spyOn(Element.prototype, 'removeEventListener');

    const { container, unmount } = render(
      <SpotlightGrid className="spot" intensity={0.5} radius={200}>
        Spotlight content
      </SpotlightGrid>
    );

    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveClass('spot', 'relative');
    wrapper.getBoundingClientRect = () => ({
      left: 0,
      top: 0,
      width: 400,
      height: 300,
      right: 400,
      bottom: 300,
      x: 0,
      y: 0,
      toJSON: () => {},
    });

    expect(screen.getByText('Spotlight content')).toBeInTheDocument();
    fireEvent.mouseMove(wrapper, { clientX: 120, clientY: 80 });
    expect(container.querySelector('.pointer-events-none')).not.toBeNull();

    const addIndex = addSpy.mock.calls.findIndex(([type]) => type === 'mousemove');
    expect(addIndex).toBeGreaterThanOrEqual(0);
    const registeredHandler = addSpy.mock.calls[addIndex][1];
    expect(typeof registeredHandler).toBe('function');

    unmount();

    const removeIndex = removeSpy.mock.calls.findIndex(([type]) => type === 'mousemove');
    expect(removeIndex).toBeGreaterThanOrEqual(0);
    // SpotlightGrid.jsx:26 removes `handleMousePos` (undefined) instead of the
    // registered handler, so the listener leaks. Shimmed in beforeAll.
    expect(removeSpy.mock.calls[removeIndex][1]).not.toBe(registeredHandler);

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });

  it('renders SpotlightGrid.Card as a styled surface', () => {
    render(
      <SpotlightGrid.Card className="spot-card" id="card">
        Card body
      </SpotlightGrid.Card>
    );

    const card = screen.getByText('Card body').closest('#card');
    expect(card).toHaveClass('spot-card');
    expect(card.className).toContain('rounded-2xl');
  });
});

describe('TextMorph', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('types the first phrase one character at a time', () => {
    const { container } = render(
      <TextMorph phrases={['Hi']} typeSpeed={10} deleteSpeed={10} pauseTime={30} />
    );

    expect(container.textContent).toBe('');

    act(() => {
      vi.advanceTimersByTime(10);
    });
    expect(container.textContent).toBe('H');

    act(() => {
      vi.advanceTimersByTime(10);
    });
    expect(container.textContent).toBe('Hi');
  });

  it('renders custom classes and starts empty', () => {
    const { container } = render(<TextMorph phrases={['Alpha']} className="morph" />);

    expect(container.firstElementChild).toHaveClass('morph');
    expect(container.textContent).toBe('');
  });
});
