import { Component } from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import ThemeProvider, {
  applyThemeToDocument,
  useTheme,
} from '../../components/common/ThemeProvider';

const { mockAppContext } = vi.hoisted(() => ({
  mockAppContext: { theme: 'light', toggleTheme: vi.fn() },
}));

vi.mock('../../context/AppContext', () => ({
  useAppContext: () => mockAppContext,
}));

const Probe = () => {
  const { theme, isDark, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="is-dark">{String(isDark)}</span>
      <button type="button" onClick={toggleTheme}>
        Toggle theme
      </button>
    </div>
  );
};

class Catcher extends Component {
  constructor(props) {
    super(props);
    this.state = { message: '' };
  }

  static getDerivedStateFromError(error) {
    return { message: error.message };
  }

  render() {
    return this.state.message ? <p role="alert">{this.state.message}</p> : this.props.children;
  }
}

function stubMatchMedia(matches = false) {
  const mql = {
    matches,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal('matchMedia', vi.fn(() => mql));
  return mql;
}

describe('applyThemeToDocument', () => {
  it('applies dark and light classes plus the colour-scheme hint', () => {
    applyThemeToDocument('dark');
    expect(document.documentElement).toHaveClass('dark');
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    expect(document.documentElement.style.colorScheme).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');

    applyThemeToDocument('light');
    expect(document.documentElement).toHaveClass('light');
    expect(document.documentElement).not.toHaveClass('dark');
    expect(document.documentElement.style.colorScheme).toBe('light');
    expect(localStorage.getItem('theme')).toBe('light');
  });

  it('treats an unknown theme as light', () => {
    applyThemeToDocument('dark');
    applyThemeToDocument('sepia');

    expect(document.documentElement).toHaveClass('light');
    expect(document.documentElement).not.toHaveClass('dark');
  });
});

describe('ThemeProvider', () => {
  let mql;

  beforeEach(() => {
    mockAppContext.theme = 'light';
    mockAppContext.toggleTheme.mockClear();
    // The applyThemeToDocument describe above persists themes ('sepia'); reset
    // storage so each provider test starts from a clean slate.
    localStorage.clear();
    mql = stubMatchMedia(false);
  });

  afterEach(() => {
    document.documentElement.className = '';
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.style.colorScheme = '';
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('syncs the active theme to the document and exposes it through useTheme', () => {
    mockAppContext.theme = 'dark';
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );

    expect(document.documentElement).toHaveClass('dark');
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
    // First paint must NOT persist — a stored key would make the OS-preference
    // listener above unreachable. User toggles persist (covered below).
    expect(localStorage.getItem('theme')).toBeNull();
    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    expect(screen.getByTestId('is-dark')).toHaveTextContent('true');
  });

  it('updates the document when the app theme changes', () => {
    mockAppContext.theme = 'dark';
    const { rerender } = render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );
    expect(document.documentElement).toHaveClass('dark');

    mockAppContext.theme = 'light';
    rerender(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );

    expect(document.documentElement).toHaveClass('light');
    expect(document.documentElement).not.toHaveClass('dark');
    expect(screen.getByTestId('is-dark')).toHaveTextContent('false');
  });

  it('forwards toggleTheme to consumers', () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Toggle theme' }));
    expect(mockAppContext.toggleTheme).toHaveBeenCalledTimes(1);
  });

  it('follows the OS preference once no explicit theme is stored', () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );
    expect(document.documentElement).toHaveClass('light');

    const changeHandler = mql.addEventListener.mock.calls[0][1];
    localStorage.removeItem('theme');
    act(() => {
      changeHandler({ matches: true });
    });

    expect(document.documentElement).toHaveClass('dark');
    // System-driven changes apply but do NOT persist, so the app keeps
    // following the OS until the user makes an explicit choice.
    expect(localStorage.getItem('theme')).toBeNull();
  });

  it('ignores OS preference changes when the user chose a theme', () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );
    const changeHandler = mql.addEventListener.mock.calls[0][1];

    localStorage.setItem('theme', 'light');
    act(() => {
      changeHandler({ matches: true });
    });

    expect(document.documentElement).toHaveClass('light');
  });

  it('unsubscribes from the media query on unmount', () => {
    const { unmount } = render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );
    const changeHandler = mql.addEventListener.mock.calls[0][1];

    unmount();
    expect(mql.removeEventListener).toHaveBeenCalledWith('change', changeHandler);
  });

  it('rejects useTheme outside a ThemeProvider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <Catcher>
        <Probe />
      </Catcher>
    );

    expect(screen.getByRole('alert')).toHaveTextContent(
      'useTheme must be used within a ThemeProvider'
    );
    consoleError.mockRestore();
  });
});
