import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AppContext } from '../../context/AppContext';
import { NotificationProvider, useNotifications } from '../../context/NotificationContext';

describe('NotificationContext', () => {
  it('exposes the app notification state and actions', () => {
    const notifications = [{ id: 1, message: 'Saved', type: 'success' }];
    const addNotification = vi.fn();
    const dismissNotification = vi.fn();
    const appContext = { notifications, addNotification, dismissNotification };
    const wrapper = ({ children }) => (
      <AppContext.Provider value={appContext}>
        <NotificationProvider>{children}</NotificationProvider>
      </AppContext.Provider>
    );
    const { result } = renderHook(() => useNotifications(), { wrapper });

    expect(result.current.notifications).toBe(notifications);
    expect(result.current.addNotification).toBe(addNotification);
    expect(result.current.dismissNotification).toBe(dismissNotification);
  });
});
