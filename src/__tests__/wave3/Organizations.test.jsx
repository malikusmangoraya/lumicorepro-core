import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OrganizationsPage from '../../pages/Organizations';

vi.mock('@/components/ui', async (importOriginal) => {
  const actual = await importOriginal();
  const React = await import('react');
  const withoutIcons = (props) => {
    const next = { ...props };
    delete next.leftIcon;
    delete next.rightIcon;
    return next;
  };
  return {
    ...actual,
    Input: (props) => React.createElement(actual.Input, withoutIcons(props)),
    Button: (props) => React.createElement(actual.Button, withoutIcons(props)),
  };
});

const { orgState, appState } = vi.hoisted(() => ({
  orgState: {
    orgs: [],
    current: null,
    loading: false,
    error: null,
    createOrg: vi.fn(),
    switchOrg: vi.fn(),
  },
  appState: { addNotification: vi.fn() },
}));

vi.mock('../../context/OrgContext', () => ({ useOrg: () => orgState }));
vi.mock('../../context/AppContext', () => ({ useAppContext: () => appState }));

const ORGS = [
  { org: { id: 1, name: 'Acme Studios' }, role: 'owner', status: 'active' },
  { org: { id: 2, name: 'Beta Labs' }, role: 'member', status: 'invited' },
];

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/orgs']}>
      <OrganizationsPage />
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  orgState.orgs = ORGS;
  orgState.current = { id: 1 };
  orgState.loading = false;
  orgState.error = null;
  orgState.createOrg.mockResolvedValue({ id: 3, name: 'New Studio' });
});

describe('Organizations page', () => {
  it('lists the memberships, marks the active one and offers switching', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: /Organizations/ })).toBeInTheDocument();
    expect(screen.getByText('Acme Studios')).toBeInTheDocument();
    expect(screen.getByText('Beta Labs')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('owner · active')).toBeInTheDocument();
    expect(screen.getByText('member · invited')).toBeInTheDocument();

    const manageLinks = screen.getAllByRole('link', { name: 'Manage' });
    expect(manageLinks).toHaveLength(2);
    expect(manageLinks[0]).toHaveAttribute('href', '/orgs/1');

    const switchButtons = screen.getAllByRole('button', { name: 'Switch' });
    expect(switchButtons).toHaveLength(1);
    fireEvent.click(switchButtons[0]);
    expect(orgState.switchOrg).toHaveBeenCalledWith(2);
  });

  it('renders the empty state when the user has no organizations', () => {
    orgState.orgs = [];
    renderPage();

    expect(
      screen.getByText('No organizations yet. Create one above to get started.')
    ).toBeInTheDocument();
  });

  it('validates the name, then creates the organization and notifies', async () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /Create Organization/i }));
    expect(screen.getAllByText('Organization name is required').length).toBeGreaterThan(0);
    expect(orgState.createOrg).not.toHaveBeenCalled();

    const input = screen.getByLabelText('Organization name');
    fireEvent.change(input, { target: { value: '  New Studio  ' } });
    fireEvent.click(screen.getByRole('button', { name: /Create Organization/i }));

    await waitFor(() => expect(orgState.createOrg).toHaveBeenCalledWith('New Studio'));
    expect(appState.addNotification).toHaveBeenCalledWith('Organization created', 'success');
    await waitFor(() => expect(input).toHaveValue(''));
  });

  it('surfaces a create failure without losing the form', async () => {
    orgState.createOrg.mockRejectedValue({
      response: { data: { error: 'Name already taken' } },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText('Organization name'), {
      target: { value: 'Acme Studios' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Create Organization/i }));

    expect((await screen.findAllByText('Name already taken')).length).toBeGreaterThan(0);
    expect(screen.getByLabelText('Organization name')).toHaveValue('Acme Studios');
    expect(orgState.createOrg).toHaveBeenCalledTimes(1);
  });
});
