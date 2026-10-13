export const DESIGN_STYLES = {
  minimalism: {
    id: 'minimalism',
    name: 'Minimalism',
    description: 'Clean, simple, maximum whitespace, essential elements only',
    tokens: {
      spacing: {
        scale: 0.75,
        containerPadding: '1.5rem',
        sectionGap: '3rem',
        componentGap: '1rem',
      },
      typography: {
        scale: 0.9,
        headingWeight: 400,
        letterSpacing: '0.02em',
        lineHeight: 1.7,
      },
      radius: {
        scale: 0.5,
        base: '0.25rem',
      },
      shadows: {
        intensity: 0.3,
        elevation: 'flat',
      },
      borders: {
        width: '1px',
        opacity: 0.1,
      },
      motion: {
        duration: 0.5,
        easing: 'ease-out',
        reduced: true,
      },
      density: 'comfortable',
      decorativeElements: false,
      gradients: false,
      glassmorphism: false,
    },
    components: {
      Button: { variant: 'outline', size: 'sm', padding: '0.5rem 1rem' },
      Card: { padding: '1rem', shadow: 'none', border: true },
      Input: { padding: '0.5rem 0.75rem', borderWidth: '1px' },
      Badge: { minimal: true },
    },
  },

  maximalism: {
    id: 'maximalism',
    name: 'Maximalism',
    description: 'Rich, dense, decorative, layered visual hierarchy',
    tokens: {
      spacing: {
        scale: 1.25,
        containerPadding: '2.5rem',
        sectionGap: '5rem',
        componentGap: '1.5rem',
      },
      typography: {
        scale: 1.15,
        headingWeight: 700,
        letterSpacing: '-0.01em',
        lineHeight: 1.3,
      },
      radius: {
        scale: 1.5,
        base: '1rem',
      },
      shadows: {
        intensity: 1.5,
        elevation: 'layered',
      },
      borders: {
        width: '2px',
        opacity: 0.3,
      },
      motion: {
        duration: 1.0,
        easing: 'spring',
        reduced: false,
      },
      density: 'dense',
      decorativeElements: true,
      gradients: true,
      glassmorphism: true,
    },
    components: {
      Button: { variant: 'gradient', size: 'lg', padding: '1rem 2rem' },
      Card: { padding: '2rem', shadow: 'xl', border: false },
      Input: { padding: '0.75rem 1rem', borderWidth: '2px' },
      Badge: { decorative: true },
    },
  },

  balanced: {
    id: 'balanced',
    name: 'Balanced',
    description: 'Harmonious middle ground — professional and engaging',
    tokens: {
      spacing: {
        scale: 1.0,
        containerPadding: '2rem',
        sectionGap: '4rem',
        componentGap: '1.25rem',
      },
      typography: {
        scale: 1.0,
        headingWeight: 600,
        letterSpacing: '0',
        lineHeight: 1.5,
      },
      radius: {
        scale: 1.0,
        base: '0.5rem',
      },
      shadows: {
        intensity: 1.0,
        elevation: 'moderate',
      },
      borders: {
        width: '1px',
        opacity: 0.15,
      },
      motion: {
        duration: 0.7,
        easing: 'spring',
        reduced: false,
      },
      density: 'normal',
      decorativeElements: true,
      gradients: true,
      glassmorphism: false,
    },
    components: {
      Button: { variant: 'default', size: 'md', padding: '0.75rem 1.5rem' },
      Card: { padding: '1.5rem', shadow: 'md', border: true },
      Input: { padding: '0.625rem 0.875rem', borderWidth: '1px' },
      Badge: { standard: true },
    },
  },

  editorial: {
    id: 'editorial',
    name: 'Editorial',
    description: 'Magazine-style, strong typography, asymmetric layouts',
    tokens: {
      spacing: {
        scale: 1.1,
        containerPadding: '2rem',
        sectionGap: '4.5rem',
        componentGap: '1.5rem',
      },
      typography: {
        scale: 1.1,
        headingWeight: 800,
        letterSpacing: '-0.02em',
        lineHeight: 1.2,
      },
      radius: {
        scale: 0.3,
        base: '0.125rem',
      },
      shadows: {
        intensity: 0.4,
        elevation: 'flat',
      },
      borders: {
        width: '2px',
        opacity: 0.5,
      },
      motion: {
        duration: 0.8,
        easing: 'ease-in-out',
        reduced: true,
      },
      density: 'normal',
      decorativeElements: false,
      gradients: false,
      glassmorphism: false,
    },
    components: {
      Button: { variant: 'outline', size: 'md', uppercase: true },
      Card: { padding: '1.5rem', border: 'thick' },
      Input: { padding: '0.75rem', borderWidth: '2px' },
      Badge: { editorial: true },
    },
  },
};

export const LAYOUT_TYPES = {
  standard: {
    id: 'standard',
    name: 'Standard',
    description: 'Classic centered container with consistent spacing',
    container: { maxWidth: '1280px', padding: '1.5rem' },
    grid: { columns: 12, gap: '1.5rem' },
    sidebar: { width: '280px', collapsible: true },
    header: { height: 'auto', sticky: true },
    footer: { style: 'multi-column' },
  },

  narrow: {
    id: 'narrow',
    name: 'Narrow',
    description: 'Tight reading width for content-focused layouts',
    container: { maxWidth: '720px', padding: '1rem' },
    grid: { columns: 8, gap: '1rem' },
    sidebar: { width: '240px', collapsible: true },
    header: { height: 'auto', sticky: false },
    footer: { style: 'minimal' },
  },

  wide: {
    id: 'wide',
    name: 'Wide',
    description: 'Full-width immersive layouts for dashboards and apps',
    container: { maxWidth: '100%', padding: '2rem' },
    grid: { columns: 16, gap: '2rem' },
    sidebar: { width: '320px', collapsible: false },
    header: { height: '64px', sticky: true },
    footer: { style: 'compact' },
  },

  split: {
    id: 'split',
    name: 'Split View',
    description: 'Two-pane layout with persistent sidebar/navigation',
    container: { maxWidth: '100%', padding: 0 },
    grid: { columns: 12, gap: 0 },
    sidebar: { width: '300px', collapsible: true, persistent: true },
    header: { height: '60px', sticky: true, shared: true },
    footer: { style: 'hidden' },
  },

  masonry: {
    id: 'masonry',
    name: 'Masonry',
    description: 'Pinterest-style fluid grid for visual content',
    container: { maxWidth: '100%', padding: '1rem' },
    grid: { columns: 'auto-fit', gap: '1rem', masonry: true },
    sidebar: { width: '0', collapsible: false },
    header: { height: 'auto', sticky: true },
    footer: { style: 'minimal' },
  },

  bento: {
    id: 'bento',
    name: 'Bento Grid',
    description: 'Apple-style card grid with varied card sizes',
    container: { maxWidth: '1440px', padding: '2rem' },
    grid: { columns: 4, rows: 'auto', gap: '1.5rem', bento: true },
    sidebar: { width: '0', collapsible: false },
    header: { height: 'auto', sticky: false },
    footer: { style: 'minimal' },
  },
};

export const AUTO_MODE_CONFIG = {
  enabled: true,
  defaultStyle: 'balanced',
  defaultLayout: 'standard',
  persistSelection: true,
  storageKey: 'lumicore-design-prefs',
  autoDetect: {
    enabled: true,
    rules: [
      { condition: 'content-heavy', style: 'editorial', layout: 'narrow' },
      { condition: 'data-dense', style: 'minimalism', layout: 'wide' },
      { condition: 'visual-portfolio', style: 'maximalism', layout: 'masonry' },
      { condition: 'dashboard', style: 'minimalism', layout: 'split' },
      { condition: 'marketing', style: 'maximalism', layout: 'standard' },
      { condition: 'creative', style: 'editorial', layout: 'bento' },
    ],
  },
  transitions: {
    styleChange: 300,
    layoutChange: 400,
  },
  breakpoints: {
    mobile: { maxWidth: 640, forceLayout: 'narrow' },
    tablet: { maxWidth: 1024, forceLayout: null },
    desktop: { maxWidth: 1440, forceLayout: null },
  },
};

export function getDesignStyle(styleId) {
  return DESIGN_STYLES[styleId] || DESIGN_STYLES.balanced;
}

export function getLayoutType(layoutId) {
  return LAYOUT_TYPES[layoutId] || LAYOUT_TYPES.standard;
}

export function applyDesignTokens(styleId, isDark = false) {
  const style = getDesignStyle(styleId);
  const tokens = style.tokens;
  const root = document.documentElement;

  root.style.setProperty('--design-spacing-scale', tokens.spacing.scale);
  root.style.setProperty('--design-typography-scale', tokens.typography.scale);
  root.style.setProperty('--design-radius-scale', tokens.radius.scale);
  root.style.setProperty('--design-shadow-intensity', tokens.shadows.intensity);
  root.style.setProperty('--design-border-opacity', tokens.borders.opacity);
  root.style.setProperty('--design-motion-duration', `${tokens.motion.duration}s`);
  root.style.setProperty('--design-density', tokens.density);

  if (tokens.decorativeElements) {
    root.classList.add('design-decorative');
  } else {
    root.classList.remove('design-decorative');
  }
  if (tokens.gradients) {
    root.classList.add('design-gradients');
  } else {
    root.classList.remove('design-gradients');
  }
  if (tokens.glassmorphism) {
    root.classList.add('design-glassmorphism');
  } else {
    root.classList.remove('design-glassmorphism');
  }

  const radiusBase = parseFloat(tokens.radius.base) * tokens.radius.scale;
  root.style.setProperty('--radius', `${radiusBase}rem`);
  root.style.setProperty('--radius-sm', `${radiusBase * 0.5}rem`);
  root.style.setProperty('--radius-lg', `${radiusBase * 2}rem`);
  root.style.setProperty('--radius-xl', `${radiusBase * 3}rem`);

  return tokens;
}

export function applyLayoutTokens(layoutId) {
  const layout = getLayoutType(layoutId);
  const root = document.documentElement;

  root.style.setProperty('--layout-container-max', layout.container.maxWidth);
  root.style.setProperty('--layout-container-padding', layout.container.padding);
  root.style.setProperty('--layout-grid-columns', layout.grid.columns);
  root.style.setProperty('--layout-grid-gap', layout.grid.gap);
  root.style.setProperty('--layout-sidebar-width', layout.sidebar.width);
  root.style.setProperty('--layout-header-height', layout.header.height);
  root.style.setProperty('--layout-footer-style', layout.footer.style);

  if (layout.grid.masonry) root.classList.add('layout-masonry');
  else root.classList.remove('layout-masonry');
  if (layout.grid.bento) root.classList.add('layout-bento');
  else root.classList.remove('layout-bento');
  if (layout.sidebar.persistent) root.classList.add('layout-split');
  else root.classList.remove('layout-split');

  return layout;
}

export function getAutoModeConfig() {
  return AUTO_MODE_CONFIG;
}

export function detectContentType(pathname) {
  const rules = AUTO_MODE_CONFIG.autoDetect.rules;
  for (const rule of rules) {
    if (pathname.includes(rule.condition)) {
      return { style: rule.style, layout: rule.layout };
    }
  }
  return { style: AUTO_MODE_CONFIG.defaultStyle, layout: AUTO_MODE_CONFIG.defaultLayout };
}

export default {
  DESIGN_STYLES,
  LAYOUT_TYPES,
  AUTO_MODE_CONFIG,
  getDesignStyle,
  getLayoutType,
  applyDesignTokens,
  applyLayoutTokens,
  getAutoModeConfig,
  detectContentType,
};