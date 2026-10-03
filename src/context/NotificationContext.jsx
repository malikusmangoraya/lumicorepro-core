import { createContext, useContext, useMemo } from 'react';
import { useAppContext } from './AppContext';

const NotificationContext = createContext(null);

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}

export function NotificationProvider({ children }) {
  const app = useAppContext();
  const value = useMemo(
    () => ({
      notifications: app.notifications,
      addNotification: app.addNotification,
      dismissNotification: app.dismissNotification,
    }),
    [app.addNotification, app.dismissNotification, app.notifications]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export default NotificationContext;
