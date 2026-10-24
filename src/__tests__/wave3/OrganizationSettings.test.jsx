import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import OrganizationSettingsPage from '../../pages/OrganizationSettings';

/**
 * The page hands JSX elements to Input leftIcon, which the real primitive
 * renders as a component type and crashes on. Strip icons to exercise the page
 * logic (see the report: same defect as the wave2 password pages).
 */
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

const { orgState, appState, orgService } = vi.hoisted(() => ({
  orgState: { current: null, permissions: [], isManager: false },
  appState: { user: { id: 1 }, addNotification: vi.fn() },
  orgService: {
    current: vi.fn(),
    members: vi.fn(),
    roles: vi.fn(),
    invite: vi.fn(),
    updateMember: vi.fn(),
    removeMember: vi.fn(),
  },
}));

vi.mock('../../context/OrgContext', () => ({ useOrg: () => orgState }));
vi.mock('../../context/AppContext', () => ({ useAppContext: () => appState }));
vi.mock('../../services/orgs', () => ({ default: orgService }));

const MEMBERS = [
  {
    id: 1,
    userId: 2,
    name: 'Ada Lovelace',
    email: 'ada@example.com',
    role: 'member',
    status: 'active',
  },
];

const ROLES = [
  { id: 1, name: 'admin', permissions: ['org.manage', 'org.members.manage'], is_system: true },
  { id: 2, name: 'member', permissions: ['org.read'], is_system: true },
];

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/orgs/5']}>
      <Routes>
        <Route path="/orgs/:id" element={<OrganizationSettingsPage />} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  orgState.current = { id: 5 };
  orgState.permissions = ['org.manage', 'org.members.manage'];
  orgState.isManager = true;
  orgService.current.mockResolvedValue({ data: { org: { id: 5, name: 'Acme Corp' } } });
  orgService.members.mockResolvedValue({ data: { members: MEMBERS } });
  orgService.roles.mockResolvedValue({ data: { roles: ROLES } });
  orgService.invite.mockResolvedValue({ data: {} });
});

describe('OrganizationSettings page', () => {
  it('renders the organization, members, roles and invite form for managers', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { level: 1, name: /Acme Corp/ })).toBeInTheDocument();
    expect(screen.getByText('Active workspace')).toBeInTheDocument();
    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument();
    expect(screen.getByText('ada@example.com')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('org.manage')).toBeInTheDocument();
    expect(screen.getByText('org.read')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Invite' })).toBeInTheDocument();
    expect(orgService.current).toHaveBeenCalledTimes(1);
    expect(orgService.members).toHaveBeenCalledWith('5');
    expect(orgService.roles).toHaveBeenCalledWith('5');
  });

  it('validates the invite email, then sends it and reloads the data', async () => {
    renderPage();
    await screen.findByRole('heading', { level: 1, name: /Acme Corp/ });

    fireEvent.click(screen.getByRole('button', { name: 'Invite' }));
    expect(orgService.invite).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: '  new@example.com  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Invite' }));

    await waitFor(() =>
      expect(orgService.invite).toHaveBeenCalledWith('5', 'new@example.com', 'member')
    );
    expect(appState.addNotification).toHaveBeenCalledWith('Invitation sent', 'success');
    await waitFor(() => expect(orgService.current).toHaveBeenCalledTimes(2));
  });

  it('renders a read-only view for non-managers without invite controls', async () => {
    orgState.isManager = false;
    orgState.permissions = [];
    renderPage();

    await screen.findByText('Ada Lovelace');
    expect(screen.getByText(/view access/i)).toBeInTheDocument();
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Invite' })).not.toBeInTheDocument();
    expect(screen.getByText(/none in this workspace/)).toBeInTheDocument();
  });

  it('shows the load error while still rendering the shell', async () => {
    orgState.permissions = [];
    orgService.members.mockRejectedValue({
      response: { data: { error: 'Organization not found' } },
    });
    renderPage();

    expect(await screen.findByText('Organization not found')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: /Organization/ })).toBeInTheDocument();
    expect(screen.queryByText('Ada Lovelace')).not.toBeInTheDocument();
  });
});
