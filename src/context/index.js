export { AppContext, useAppContext, AppProvider } from './AppContext';
export { default as AuthContext, AuthProvider, useAuth } from './AuthContext';
export { default as OrgContext, OrgProvider, useOrg } from './OrgContext';
// Cart moved to Zustand: `store/cartStore.js` (useCart / useCartStore / useCartTotals).
export { CurrencyContext, CurrencyProvider } from './CurrencyContext';
export {
  default as NotificationContext,
  NotificationProvider,
  useNotifications,
} from './NotificationContext';
// ThemeContext is a thin pass-through over AppContext — use useAppContext() directly
export { ThemeContext, useTheme, ThemeProvider } from './ThemeContext';
