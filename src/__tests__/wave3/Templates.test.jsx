import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TemplatesHub from '../../pages/Templates';
import { TEMPLATE_CATALOG } from '../../templates/catalog';
import { FILTER_SCOPES, useFilterStore } from '../../store/filterStore';

/**
 * 60 framer-motion cards make a full render exceed the 15s test timeout. The
 * Card wrapper is not what this suite asserts on, so render a plain clickable
 * container with the same contract (onClick -> role="button").
 */
vi.mock('@/components/ui/Card', async () => {
  const React = await import('react');
  return {
    default: ({ children, className, onClick }) =>
      React.createElement(
        'div',
        {
          className,
          onClick,
          role: onClick ? 'button' : undefined,
          tabIndex: onClick ? 0 : undefined,
        },
        children
      ),
  };
});

const renderTemplates = () =>
  render(
    <MemoryRouter initialEntries={['/templates']}>
      <Routes>
        <Route path="/templates" element={<TemplatesHub />} />
        <Route
          path="/templates/ecommerce/ProductListing"
          element={<div>product-listing-route</div>}
        />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  // The hub keeps filters in a Zustand store, which outlives an individual test.
  useFilterStore.getState().resetFilters(FILTER_SCOPES.TEMPLATES);
});

describe('Templates page', () => {
  it('renders the header, search field and all catalog cards', () => {
    renderTemplates();

    expect(screen.getByRole('heading', { level: 1, name: 'Template Gallery' })).toBeTruthy();
    expect(screen.getByText('60 Templates')).toBeTruthy();
    expect(screen.getByText('12 Categories')).toBeTruthy();
    expect(screen.getByRole('textbox', { name: 'Search templates' })).toHaveValue('');
    expect(screen.getAllByRole('heading', { level: 2, hidden: true })).toHaveLength(12);
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(
      TEMPLATE_CATALOG.length
    );
    expect(screen.getByRole('button', { name: 'All 60' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
  }, 45000);

  it('filters the grid by category and marks the active tab', () => {
    renderTemplates();

    fireEvent.click(screen.getByRole('button', { name: 'Dashboard 5' }));

    expect(screen.getByRole('heading', { level: 2, name: 'Dashboard' })).toBeTruthy();
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(5);
    expect(screen.getByRole('heading', { level: 3, name: 'Dashboard Overview' })).toBeTruthy();
    expect(screen.queryByRole('heading', { level: 3, name: 'Product Listing' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Dashboard 5' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    expect(screen.getByRole('button', { name: 'All 60' })).toHaveAttribute(
      'aria-pressed',
      'false'
    );
  }, 45000);

  it('searches titles/descriptions and clears the query', () => {
    renderTemplates();

    const search = screen.getByRole('textbox', { name: 'Search templates' });
    fireEvent.change(search, { target: { value: 'Product Listing' } });

    expect(search).toHaveValue('Product Listing');
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(1);
    expect(screen.getByRole('heading', { level: 3, name: 'Product Listing' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Clear search' }));

    expect(search).toHaveValue('');
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(
      TEMPLATE_CATALOG.length
    );
  });

  it('opens a template preview through the card click target', () => {
    renderTemplates();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search templates' }), {
      target: { value: 'Product Listing' },
    });
    fireEvent.click(screen.getByRole('heading', { level: 3, name: 'Product Listing' }));

    expect(screen.getByText('product-listing-route')).toBeTruthy();
  });

  it('shows the empty state and recovers via Clear filters', () => {
    renderTemplates();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search templates' }), {
      target: { value: 'no-such-template-xyz' },
    });

    // Only the empty-state heading remains once nothing matches.
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(1);
    expect(screen.getByText('No templates found')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }));

    expect(screen.queryByText('No templates found')).toBeNull();
    expect(screen.getByRole('textbox', { name: 'Search templates' })).toHaveValue('');
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(
      TEMPLATE_CATALOG.length
    );
  });
});
