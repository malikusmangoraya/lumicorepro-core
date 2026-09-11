import { createContext, useContext, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';

const ThemeContext = createContext(undefined);

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export const applyThemeToDocument = (theme) => {
  const root = document.documentElement;
  root.classList.remove('light', 'dark');
  root.classList.add(theme === 'dark' ? 'dark' : 'light');
  root.setAttribute('data-theme', theme);
  root.style.colorScheme = theme;
  localStorage.setItem('theme', theme);
};

export default function ThemeProvider({ children }) {
  const { theme, toggleTheme } = useAppContext();

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => {
      if (!localStorage.getItem('theme')) {
        applyThemeToDocument(e.matches ? 'dark' : 'light');
      }
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  return (
    <ThemeContext.Provider
      value={{ theme, setTheme: toggleTheme, toggleTheme, isDark: theme === 'dark' }}
    >
      {children}
    </ThemeContext.Provider>
  );
}
