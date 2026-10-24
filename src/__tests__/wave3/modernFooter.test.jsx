import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const queryState = vi.hoisted(() => ({ result: { isPending: false, isError: false } }));
const postLead = vi.hoisted(() => vi.fn());

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => queryState.result,
}));

vi.mock('../../components/common/Language', () => ({ default: () => null }));
vi.mock('../../components/common/CurrencySelector', () => ({ CurrencySelector: () => null }));

vi.mock('../../services/contact', () => ({
  contactAPI: { postLead },
}));

import ModernFooter from '../../components/common/ModernFooter';

function renderFooter(props = {}) {
  return render(
    <MemoryRouter>
      <ModernFooter {...props} />
    </MemoryRouter>
  );
}

beforeEach(() => {
  queryState.result = { isPending: false, isError: false };
  postLead.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ModernFooter', () => {
  it('renders the brand, four link columns, and live status', () => {
    renderFooter();

    const footer = screen.getByRole('contentinfo', { name: 'Site Footer' });
    for (const heading of ['Platform', 'Solutions', 'Resources', 'Legal & Trust']) {
      expect(within(footer).getByRole('heading', { name: heading })).toBeInTheDocument();
    }

    expect(within(footer).getByRole('link', { name: /AI Generator/ })).toHaveAttribute(
      'href',
      '/generate'
    );
    expect(within(footer).getByRole('link', { name: /Privacy Policy/ })).toHaveAttribute(
      'href',
      '/privacy'
    );
    expect(within(footer).getByText(/All rights reserved/)).toHaveTextContent(
      String(new Date().getFullYear())
    );
    expect(within(footer).getByText('API reachable — status OK')).toBeInTheDocument();
  });

  it('reflects the health query state in the status badge', () => {
    queryState.result = { isPending: true, isError: false };
    const { rerender } = renderFooter();
    expect(screen.getByText('Checking system status…')).toBeInTheDocument();

    queryState.result = { isPending: false, isError: true };
    rerender(
      <MemoryRouter>
        <ModernFooter />
      </MemoryRouter>
    );
    expect(screen.getByText('Status unavailable')).toBeInTheDocument();
  });

  it('honours custom columns and hides optional blocks', () => {
    renderFooter({
      columns: [{ title: 'Custom', links: [{ label: 'Only link', href: '/only' }] }],
      showNewsletter: false,
      showStatus: false,
    });

    expect(screen.getByRole('heading', { name: 'Custom' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Platform' })).not.toBeInTheDocument();
    expect(screen.queryByText('API reachable — status OK')).not.toBeInTheDocument();
    expect(screen.queryByText('Stay ahead of modern web design')).not.toBeInTheDocument();
  });

  it('rejects an invalid newsletter email without calling the API', () => {
    renderFooter();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'not-an-email' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Enter a valid email address.');
    expect(postLead).not.toHaveBeenCalled();
  });

  it('submits a valid newsletter email and reports an unconfigured provider honestly', async () => {
    postLead.mockResolvedValue({ mock: true });
    renderFooter();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'buyer@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(await screen.findByText(/Newsletter delivery is not configured/)).toBeInTheDocument();
    expect(postLead).toHaveBeenCalledWith(
      expect.objectContaining({ email: 'buyer@example.com', consent: true })
    );
  });

  it('reports success and surfaces API failures', async () => {
    postLead.mockResolvedValueOnce({ ok: true });
    renderFooter();

    const input = screen.getByLabelText('Email address');
    fireEvent.change(input, { target: { value: 'buyer@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(await screen.findByText('Thanks — check your inbox to confirm.')).toBeInTheDocument();
    expect(input).toHaveValue('');

    postLead.mockRejectedValueOnce(new Error('offline'));
    fireEvent.change(input, { target: { value: 'buyer@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(
      await screen.findByText('We could not submit your signup. Please try again.')
    ).toBeInTheDocument();
  });

  it('dispatches cookie preferences and scrolls back to the top', () => {
    const cookieListener = vi.fn();
    const scrollSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    window.addEventListener('cookiePreferences', cookieListener);

    renderFooter();
    fireEvent.click(screen.getByRole('button', { name: 'Cookie Preferences' }));
    expect(cookieListener).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Back to top' }));
    expect(scrollSpy).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });

    window.removeEventListener('cookiePreferences', cookieListener);
  });
});
