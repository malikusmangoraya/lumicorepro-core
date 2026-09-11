import { createContext, useContext } from 'react';
import { useAppContext } from './AppContext';

export const ThemeContext = createContext();

export function useTheme() {
  const contextValue = useContext(ThemeContext);
  try {
    const app = useAppContext();
    if (app) {
      return {
        theme: app.theme,
        setTheme: (t) => {
          if (app.theme !== t) app.toggleTheme();
        },
        toggleTheme: app.toggleTheme,
        isDark: app.isDark,
      };
    }
  } catch {
    /* fallback if used outside AppProvider */
  }
  if (contextValue) return contextValue;
  return {
    theme: 'dark',
    setTheme: () => {},
    toggleTheme: () => {},
    isDark: true,
  };
}

export function ThemeProvider({ children }) {
  return <>{children}</>;
}
