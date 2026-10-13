import { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import {
  DESIGN_STYLES,
  LAYOUT_TYPES,
  AUTO_MODE_CONFIG,
  applyDesignTokens,
  applyLayoutTokens,
  detectContentType,
} from '../config/designSystem';

const DesignSystemContext = createContext(undefined);

export function useDesignSystem() {
  const context = useContext(DesignSystemContext);
  if (!context) {
    throw new Error('useDesignSystem must be used within a DesignSystemProvider');
  }
  return context;
}

export function DesignSystemProvider({ children }) {
  const [designStyle, setDesignStyleState] = useState(() => {
    if (typeof window === 'undefined') return AUTO_MODE_CONFIG.defaultStyle;
    try {
      const saved = localStorage.getItem(AUTO_MODE_CONFIG.storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.style && DESIGN_STYLES[parsed.style]) return parsed.style;
      }
    } catch {
      // Ignore localStorage parse errors
    }
    return AUTO_MODE_CONFIG.defaultStyle;
  });

  const [layoutType, setLayoutTypeState] = useState(() => {
    if (typeof window === 'undefined') return AUTO_MODE_CONFIG.defaultLayout;
    try {
      const saved = localStorage.getItem(AUTO_MODE_CONFIG.storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.layout && LAYOUT_TYPES[parsed.layout]) return parsed.layout;
      }
    } catch {
      // Ignore localStorage parse errors
    }
    return AUTO_MODE_CONFIG.defaultLayout;
  });

  const [autoMode, setAutoMode] = useState(() => {
    if (typeof window === 'undefined') return AUTO_MODE_CONFIG.enabled;
    try {
      const saved = localStorage.getItem(AUTO_MODE_CONFIG.storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.autoMode !== undefined ? parsed.autoMode : AUTO_MODE_CONFIG.enabled;
      }
    } catch {
      // Ignore localStorage parse errors
    }
    return AUTO_MODE_CONFIG.enabled;
  });

  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return true;
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const applyStyle = useCallback((styleId, darkMode = isDark) => {
    const style = DESIGN_STYLES[styleId] || DESIGN_STYLES.balanced;
    applyDesignTokens(styleId, darkMode);
    return style;
  }, [isDark]);

  const applyLayout = useCallback((layoutId) => {
    const layout = LAYOUT_TYPES[layoutId] || LAYOUT_TYPES.standard;
    applyLayoutTokens(layoutId);
    return layout;
  }, []);

  const setDesignStyle = useCallback((styleId) => {
    if (!DESIGN_STYLES[styleId]) return;
    setDesignStyleState(styleId);
    applyStyle(styleId, isDark);
    if (AUTO_MODE_CONFIG.persistSelection) {
      try {
        const saved = localStorage.getItem(AUTO_MODE_CONFIG.storageKey) || '{}';
        const parsed = JSON.parse(saved);
        localStorage.setItem(
          AUTO_MODE_CONFIG.storageKey,
          JSON.stringify({ ...parsed, style: styleId })
        );
      } catch {
        // Ignore localStorage write errors
      }
    }
  }, [applyStyle, isDark]);

  const setLayoutType = useCallback((layoutId) => {
    if (!LAYOUT_TYPES[layoutId]) return;
    setLayoutTypeState(layoutId);
    applyLayout(layoutId);
    if (AUTO_MODE_CONFIG.persistSelection) {
      try {
        const saved = localStorage.getItem(AUTO_MODE_CONFIG.storageKey) || '{}';
        const parsed = JSON.parse(saved);
        localStorage.setItem(
          AUTO_MODE_CONFIG.storageKey,
          JSON.stringify({ ...parsed, layout: layoutId })
        );
      } catch {
        // Ignore localStorage write errors
      }
    }
  }, [applyLayout]);

  const toggleAutoMode = useCallback(() => {
    const next = !autoMode;
    setAutoMode(next);
    if (AUTO_MODE_CONFIG.persistSelection) {
      try {
        const saved = localStorage.getItem(AUTO_MODE_CONFIG.storageKey) || '{}';
        const parsed = JSON.parse(saved);
        localStorage.setItem(
          AUTO_MODE_CONFIG.storageKey,
          JSON.stringify({ ...parsed, autoMode: next })
        );
      } catch {
        // Ignore localStorage write errors
      }
    }
  }, [autoMode]);

  const toggleDarkMode = useCallback(() => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', next ? 'dark' : 'light');
    applyStyle(designStyle, next);
  }, [isDark, designStyle, applyStyle]);

  useEffect(() => {
    applyStyle(designStyle, isDark);
    applyLayout(layoutType);
  }, [designStyle, layoutType, isDark, applyStyle, applyLayout]);

  useEffect(() => {
    if (!autoMode || !AUTO_MODE_CONFIG.autoDetect.enabled) return;
    if (typeof window === 'undefined') return;

    const handleRouteChange = () => {
      const { style, layout } = detectContentType(window.location.pathname);
      setDesignStyleState(style);
      setLayoutTypeState(layout);
      applyStyle(style, isDark);
      applyLayout(layout);
    };

    handleRouteChange();
    window.addEventListener('popstate', handleRouteChange);
    return () => window.removeEventListener('popstate', handleRouteChange);
  }, [autoMode, isDark, applyStyle, applyLayout]);

  const value = useMemo(
    () => ({
      designStyle,
      setDesignStyle,
      layoutType,
      setLayoutType,
      autoMode,
      toggleAutoMode,
      isDark,
      toggleDarkMode,
      availableStyles: Object.values(DESIGN_STYLES),
      availableLayouts: Object.values(LAYOUT_TYPES),
      currentStyleConfig: DESIGN_STYLES[designStyle],
      currentLayoutConfig: LAYOUT_TYPES[layoutType],
    }),
    [
      designStyle,
      layoutType,
      autoMode,
      isDark,
      setDesignStyle,
      setLayoutType,
      toggleAutoMode,
      toggleDarkMode,
    ]
  );

  return (
    <DesignSystemContext.Provider value={value}>
      {children}
    </DesignSystemContext.Provider>
  );
}

export default DesignSystemProvider;