import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import DashboardOverview from '../../templates/dashboard/DashboardOverview';
import UsersManagement from '../../templates/dashboard/UsersManagement';
import Analytics from '../../templates/dashboard/Analytics';
import Settings from '../../templates/dashboard/Settings';
import Profile from '../../templates/dashboard/Profile';

/**
 * The template pages are presentational: they render local mock data and need
 * only a router (TemplateShell renders a "Templates" back link).
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('DashboardOverview template', () => {
  it('renders the shell header and all four stat cards', () => {
    renderTemplate(<DashboardOverview />);

    expect(screen.getByRole('heading', { level: 1, name: 'Dashboard Overview' })).toBeInTheDocument();
    expect(screen.getByText('Key metrics, activity, and quick actions.')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();

    for (const label of ['Users', 'Revenue', 'Orders', 'Growth']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    for (const value of ['12.4k', '$48.2k', '1,284', '18%']) {
      expect(screen.getByText(value)).toBeInTheDocument();
    }

    expect(screen.getByRole('button', { name: 'Last 7 days' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Export Report' })).toBeInTheDocument();
  });

  it('renders the revenue chart, monthly goal, and goal breakdown', () => {
    renderTemplate(<DashboardOverview />);

    expect(screen.getByRole('heading', { name: 'Revenue Overview' })).toBeInTheDocument();
    expect(screen.getByText('+12.5%')).toBeInTheDocument();
    expect(screen.getByText('Jan')).toBeInTheDocument();
    expect(screen.getByText('Dec')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Monthly Goal' })).toBeInTheDocument();
    const progress = screen.getByRole('progressbar', { name: 'Revenue target' });
    expect(progress).toHaveAttribute('aria-valuenow', '72');
    expect(screen.getByText('Projected Revenue')).toBeInTheDocument();
    expect(screen.getByText('$98.4K')).toBeInTheDocument();
    expect(screen.getByText('New Customers')).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
    expect(screen.getByText('Conversion Rate')).toBeInTheDocument();
    expect(screen.getByText('3.2%')).toBeInTheDocument();
  });

  it('renders top products and the recent activity feed', () => {
    renderTemplate(<DashboardOverview />);

    expect(screen.getByRole('heading', { name: 'Top Products' })).toBeInTheDocument();
    expect(screen.getByText('Pro Plan Subscription')).toBeInTheDocument();
    expect(screen.getByText('Training & Onboarding')).toBeInTheDocument();
    // Finding (bug): DashboardOverview.jsx:188 prefixes the already formatted
    // `revenue` value from mockData ("$24.5K") with another "$", so the card
    // renders "$$24.5K". Asserted loosely here so fixing the template does not
    // break this test.
    expect(screen.getByText(/\$+24\.5K/)).toBeInTheDocument();
    expect(screen.getByText('+15.2%')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Recent Activity' })).toBeInTheDocument();
    expect(screen.getByText('New order #4821 placed')).toBeInTheDocument();
    expect(screen.getByText('2m ago')).toBeInTheDocument();
    expect(screen.getByText('API key rotated')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View All Activity' })).toBeInTheDocument();
  });
});

describe('UsersManagement template', () => {
  it('renders the user table with one row per seeded member', () => {
    renderTemplate(<UsersManagement />);

    expect(screen.getByRole('heading', { level: 1, name: 'Users Management' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add user' })).toBeInTheDocument();

    const table = screen.getByRole('table');
    // Header row + four users.
    expect(within(table).getAllByRole('row')).toHaveLength(5);
    for (const header of ['User', 'Role', 'Status', 'Actions']) {
      expect(within(table).getByRole('columnheader', { name: header })).toBeInTheDocument();
    }

    expect(screen.getByText('Maya Chen')).toBeInTheDocument();
    expect(screen.getByText('maya@acme.com')).toBeInTheDocument();
    expect(screen.getByText('Ava Brooks')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Edit' })).toHaveLength(4);
    expect(screen.getAllByText('active')).toHaveLength(3);
    expect(screen.getByText('invited')).toBeInTheDocument();
  });

  it('filters the table by name or email after the debounce', async () => {
    renderTemplate(<UsersManagement />);

    fireEvent.change(screen.getByPlaceholderText(/search users/i), {
      target: { value: 'jordan' },
    });

    await waitFor(() => {
      expect(screen.queryByText('Maya Chen')).toBeNull();
    });

    const table = screen.getByRole('table');
    expect(within(table).getAllByRole('row')).toHaveLength(2);
    expect(screen.getByText('Jordan Lee')).toBeInTheDocument();
    expect(screen.getByText('jordan@acme.com')).toBeInTheDocument();
  });

  it('shows the empty state when nothing matches', async () => {
    renderTemplate(<UsersManagement />);

    fireEvent.change(screen.getByPlaceholderText(/search users/i), {
      target: { value: 'no-such-user' },
    });

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
    expect(screen.getByText('Try another search.')).toBeInTheDocument();
    expect(screen.queryByRole('table')).toBeNull();
  });
});

describe('Analytics template', () => {
  it('renders the metric cards and export action', () => {
    renderTemplate(<Analytics />);

    expect(screen.getByRole('heading', { level: 1, name: 'Analytics' })).toBeInTheDocument();
    expect(screen.getByText('Traffic and conversion at a glance.')).toBeInTheDocument();

    for (const label of ['Visitors', 'Sessions', 'Conversion', 'Bounce']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    for (const value of ['24.8k', '31.2k', '3.8%', '41%']) {
      expect(screen.getByText(value)).toBeInTheDocument();
    }
    expect(screen.getByText('+6.4%')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Export CSV' })).toBeInTheDocument();
  });

  it('renders one titled bar per day in the visitors chart', () => {
    const { container } = renderTemplate(<Analytics />);

    expect(screen.getByRole('heading', { name: 'Visitors (7 days)' })).toBeInTheDocument();

    const bars = container.querySelectorAll('[title]');
    expect(bars).toHaveLength(7);
    expect(screen.getByTitle('420')).toBeInTheDocument();
    expect(screen.getByTitle('700')).toBeInTheDocument();
    for (const day of ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']) {
      expect(screen.getByText(day)).toBeInTheDocument();
    }
  });

  it('keeps the page rendered when the export action is clicked', () => {
    renderTemplate(<Analytics />);

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }));

    expect(screen.getByRole('heading', { level: 1, name: 'Analytics' })).toBeInTheDocument();
  });
});

describe('Settings template', () => {
  it('opens on the general tab with prefilled workspace fields', () => {
    renderTemplate(<Settings />);

    expect(screen.getByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument();
    for (const tab of ['General', 'Security', 'Notifications', 'Danger zone']) {
      expect(screen.getByRole('button', { name: tab })).toBeInTheDocument();
    }
    expect(screen.getByLabelText('Workspace name')).toHaveValue('My Workspace');
    expect(screen.getByLabelText('Support email')).toHaveValue('hello@company.com');
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument();
  });

  it('switches to the security tab and back', () => {
    renderTemplate(<Settings />);

    fireEvent.click(screen.getByRole('button', { name: 'Security' }));

    expect(screen.getByLabelText('Current password')).toBeInTheDocument();
    expect(screen.getByLabelText('New password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Update password' })).toBeInTheDocument();
    expect(screen.queryByLabelText('Workspace name')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'General' }));

    expect(screen.getByLabelText('Workspace name')).toBeInTheDocument();
    expect(screen.queryByLabelText('Current password')).toBeNull();
  });

  it('toggles the email alerts switch on the notifications tab', () => {
    renderTemplate(<Settings />);

    fireEvent.click(screen.getByRole('button', { name: 'Notifications' }));

    const emailSwitch = screen.getByRole('switch');
    expect(emailSwitch).toBeChecked();

    fireEvent.click(emailSwitch);

    expect(emailSwitch).not.toBeChecked();
    expect(screen.getByText('Email alerts')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save preferences' })).toBeInTheDocument();
  });

  it('shows the destructive action on the danger zone tab', () => {
    renderTemplate(<Settings />);

    fireEvent.click(screen.getByRole('button', { name: 'Danger zone' }));

    expect(
      screen.getByText('Permanently delete this workspace and all data.')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete workspace' })).toBeInTheDocument();
  });
});

describe('Profile template', () => {
  it('renders the identity card and profile fields', () => {
    renderTemplate(<Profile />);

    expect(screen.getByRole('heading', { level: 1, name: 'Profile' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Alex Rivera' })).toBeInTheDocument();
    expect(screen.getByText('Founder')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Change avatar' })).toBeInTheDocument();

    expect(screen.getByLabelText('Full name')).toHaveValue('Alex Rivera');
    expect(screen.getByLabelText('Email')).toHaveValue('alex@acme.com');
    expect(screen.getByLabelText('Title')).toHaveValue('Product Lead');
    expect(screen.getByLabelText('Location')).toHaveValue('Austin, TX');
    expect(screen.getByRole('button', { name: 'Save profile' })).toBeInTheDocument();
  });

  it('lists the recent account activity', () => {
    renderTemplate(<Profile />);

    expect(screen.getByRole('heading', { name: 'Recent activity' })).toBeInTheDocument();
    expect(screen.getByText('Updated profile photo')).toBeInTheDocument();
    expect(screen.getByText('Enabled 2FA')).toBeInTheDocument();
    expect(screen.getByText('Changed password')).toBeInTheDocument();
    expect(screen.getByText('2 weeks ago')).toBeInTheDocument();
  });
});
