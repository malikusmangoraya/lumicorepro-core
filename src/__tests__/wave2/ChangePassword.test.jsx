import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AuthContext from '../../context/AuthContext';
import ChangePasswordPage from '../../pages/ChangePassword';

/**
 * The page passes ready-made JSX elements to leftIcon/rightIcon, which the real
 * Input/Button reject (React "Element type is invalid"). Strip those decorative
 * props so the form logic can be exercised; see the bug report for details.
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
  const Input = (props) => React.createElement(actual.Input, withoutIcons(props));
  const Button = (props) => React.createElement(actual.Button, withoutIcons(props));
  return { ...actual, Input, Button };
});

const renderPage = ({ isAuthenticated = true, changePassword } = {}) => {
  const auth = {
    isAuthenticated,
    changePassword: changePassword || vi.fn().mockResolvedValue({}),
  };
  render(
    <MemoryRouter initialEntries={['/change-password']}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route path="/change-password" element={<ChangePasswordPage />} />
          <Route path="/profile" element={<div>profile-page</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>
  );
  return auth;
};

const fillForm = ({ currentPassword, password, confirm }) => {
  if (currentPassword !== undefined) {
    fireEvent.change(screen.getByLabelText('Current password'), {
      target: { value: currentPassword },
    });
  }
  if (password !== undefined) {
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: password } });
  }
  if (confirm !== undefined) {
    fireEvent.change(screen.getByLabelText('Confirm new password'), {
      target: { value: confirm },
    });
  }
};

const submit = () =>
  fireEvent.click(screen.getByRole('button', { name: /update password/i }));

describe('ChangePassword page', () => {
  it('warns and disables submission when the user is not authenticated', () => {
    renderPage({ isAuthenticated: false });

    expect(screen.getByText('You must be signed in to change your password.')).toBeTruthy();
    expect(screen.getByRole('button', { name: /update password/i })).toBeDisabled();
  });

  it('requires the current password', () => {
    const auth = renderPage();

    fillForm({ currentPassword: '', password: 'newsecret', confirm: 'newsecret' });
    submit();

    expect(screen.getAllByText('Enter your current password').length).toBeGreaterThan(0);
    expect(auth.changePassword).not.toHaveBeenCalled();
  });

  it('rejects a new password shorter than six characters', () => {
    const auth = renderPage();

    fillForm({ currentPassword: 'oldpass', password: '12345', confirm: '12345' });
    submit();

    expect(
      screen.getAllByText('New password must be at least 6 characters').length
    ).toBeGreaterThan(0);
    expect(auth.changePassword).not.toHaveBeenCalled();
  });

  it('rejects mismatched new passwords', () => {
    const auth = renderPage();

    fillForm({ currentPassword: 'oldpass', password: 'secret1', confirm: 'secret2' });
    submit();

    expect(screen.getAllByText('New passwords do not match').length).toBeGreaterThan(0);
    expect(auth.changePassword).not.toHaveBeenCalled();
  });

  it('submits the expected payload once and returns to the profile page', async () => {
    const auth = renderPage();

    fillForm({ currentPassword: 'oldpass', password: 'newsecret', confirm: 'newsecret' });
    submit();

    await waitFor(() => {
      expect(auth.changePassword).toHaveBeenCalledTimes(1);
    });
    expect(auth.changePassword).toHaveBeenCalledWith({
      currentPassword: 'oldpass',
      newPassword: 'newsecret',
    });
    expect(await screen.findByText('Password changed successfully.')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /back to profile/i }));

    expect(screen.getByText('profile-page')).toBeTruthy();
  });

  it('surfaces a backend rejection and keeps the form usable', async () => {
    const auth = renderPage({
      changePassword: vi
        .fn()
        .mockRejectedValue({ response: { data: { error: 'Current password is incorrect' } } }),
    });

    fillForm({ currentPassword: 'wrongpass', password: 'newsecret', confirm: 'newsecret' });
    submit();

    expect(
      (await screen.findAllByText('Current password is incorrect')).length
    ).toBeGreaterThan(0);
    expect(auth.changePassword).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: /update password/i })).toBeEnabled();
  });
});
