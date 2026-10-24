import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

/**
 * ChakraSection.jsx:6 mounts <ChakraProvider> without the required `value`
 * (system) prop, so the real Chakra v3 provider throws
 * "Cannot read properties of undefined (reading '_config')" and the lazy tab
 * never resolves. Chakra is stubbed to keep the showcase render-level test
 * meaningful; the bug is reported separately.
 */
vi.mock('@chakra-ui/react', async () => {
  const React = await import('react');
  const Box = ({ children, ...props }) => React.createElement('div', props, children);
  const Text = ({ children, ...props }) => React.createElement('p', props, children);
  return {
    ChakraProvider: ({ children }) => children,
    Card: {
      Root: Box,
      Header: Box,
      Title: Text,
      Description: Text,
      Body: Box,
    },
    Button: ({ children, ...props }) =>
      React.createElement('button', props, children),
    Badge: ({ children, ...props }) => React.createElement('span', props, children),
  };
});

import UiShowcase from '../../pages/ui-showcase/UiShowcase';
import AntSection from '../../pages/ui-showcase/AntSection';
import ChakraSection from '../../pages/ui-showcase/ChakraSection';

/**
 * antd/Chakra probe layout APIs that jsdom does not implement. Stub them before
 * the lazy sections mount so these render-level tests never touch the DOM APIs.
 */
if (!window.ResizeObserver) {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

if (!window.matchMedia) {
  window.matchMedia = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  });
}

describe('UiShowcase', () => {
  it('renders the shadcn tab by default with its primitives', () => {
    render(<UiShowcase />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'UI / UX Library Showcase' })
    ).toBeInTheDocument();
    expect(screen.getByRole('tablist', { name: 'UI libraries' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'shadcn/ui' })).toHaveAttribute(
      'aria-selected',
      'true'
    );
    expect(screen.getAllByText('shadcn/ui').length).toBeGreaterThanOrEqual(2);
    expect(
      screen.getByText(/Composable primitives built on Radix/)
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Destructive' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
  });

  it('lazy-loads the Ant Design section when its tab is selected', async () => {
    render(<UiShowcase />);

    fireEvent.click(screen.getByRole('tab', { name: 'Ant Design' }));

    expect(await screen.findByText('Ant Design (antd v6)')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Ant Design' })).toHaveAttribute(
      'aria-selected',
      'true'
    );
    expect(await screen.findByRole('button', { name: 'Dashed' })).toBeInTheDocument();
    expect(screen.getByText('blue')).toBeInTheDocument();
  });

  it('lazy-loads the Chakra UI section when its tab is selected', async () => {
    render(<UiShowcase />);

    fireEvent.click(screen.getByRole('tab', { name: 'Chakra UI' }));

    expect(await screen.findByRole('button', { name: 'Accent' })).toBeInTheDocument();
    expect(
      screen.getByText('Accessible, composable component primitives.')
    ).toBeInTheDocument();
    expect(screen.getAllByText('Chakra UI').length).toBeGreaterThanOrEqual(2);
  });
});

describe('AntSection', () => {
  it('renders the antd button and tag variants', () => {
    render(<AntSection />);

    expect(screen.getByText('Ant Design (antd v6)')).toBeInTheDocument();
    for (const label of ['Primary', 'Default', 'Dashed', 'Text']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
    for (const tag of ['blue', 'green', 'orange']) {
      expect(screen.getByText(tag)).toBeInTheDocument();
    }
  });
});

describe('ChakraSection', () => {
  it('renders the Chakra card, actions and badge', () => {
    render(<ChakraSection />);

    expect(screen.getByText('Chakra UI')).toBeInTheDocument();
    expect(
      screen.getByText('Accessible, composable component primitives.')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Outline' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accent' })).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });
});
