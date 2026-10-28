import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import OrbitMark from './OrbitMark.jsx';

const PAGE_META = {
  '/': {
    title: 'Orbitboard — a clearer way to plan together',
    description:
      'Explore a thoughtful roadmap-planning concept for product managers and cross-functional teams.',
  },
  '/services': {
    title: 'Features — Orbitboard',
    description: 'Explore the planning ideas behind the Orbitboard product showcase.',
  },
  '/about': {
    title: 'About — Orbitboard',
    description: 'Learn about the ideas and limits behind this Orbitboard static showcase.',
  },
  '/pricing': {
    title: 'Pricing — Orbitboard',
    description: 'See feature tiers for Orbitboard. Final pricing has not been published.',
  },
  '/contact': {
    title: 'Contact — Orbitboard',
    description: 'Find the right next step for this Orbitboard product showcase.',
  },
  '/privacy': {
    title: 'Privacy — Orbitboard',
    description: 'Understand what this static Orbitboard showcase does and does not collect.',
  },
  '/terms': {
    title: 'Terms — Orbitboard',
    description: 'Read the scope and limitations of the Orbitboard static product showcase.',
  },
  '/login': {
    title: 'Sign in — Orbitboard',
    description: 'Sign in to your Orbitboard account using the configured identity provider.',
    noIndex: true,
  },
  '/register': {
    title: 'Create an account — Orbitboard',
    description: 'Create an Orbitboard account using the configured identity provider.',
    noIndex: true,
  },
  '/reset-password': {
    title: 'Reset your password — Orbitboard',
    description: 'Set a new password for your Orbitboard account.',
    noIndex: true,
  },
  '/account': {
    title: 'Your account — Orbitboard',
    description: 'View your Orbitboard account and sign-in status.',
    noIndex: true,
  },
  '/admin': {
    title: 'Admin unavailable — Orbitboard',
    description: 'Admin tools are unavailable in this static Orbitboard showcase.',
    noIndex: true,
  },
  '/checkout': {
    title: 'Checkout unavailable — Orbitboard',
    description: 'Checkout is unavailable in this static Orbitboard showcase.',
    noIndex: true,
  },
};
const SITE_URL = 'https://malikusmangoraya.github.io/lumicorepro-core/orbitboard/';

function PageMeta() {
  const { pathname } = useLocation();

  useEffect(() => {
    const route = pathname.replace(/\/+$/, '') || '/';
    const meta = PAGE_META[route];
    const title = meta?.title ?? 'Page not found — Orbitboard';
    const description =
      meta?.description ?? 'The requested page is not part of this Orbitboard showcase.';
    const canonicalUrl = new URL(route === '/' ? '' : route.slice(1), SITE_URL).href;

    document.title = title;
    document.querySelector('meta[name="description"]')?.setAttribute('content', description);
    document.querySelector('meta[name="robots"]')?.setAttribute(
      'content',
      meta?.noIndex || !meta ? 'noindex, nofollow' : 'index, follow'
    );
    document.querySelector('link[rel="canonical"]')?.setAttribute('href', canonicalUrl);
    document.querySelector('meta[property="og:title"]')?.setAttribute('content', title);
    document.querySelector('meta[property="og:description"]')?.setAttribute('content', description);
    document.querySelector('meta[property="og:url"]')?.setAttribute('content', canonicalUrl);
  }, [pathname]);

  return null;
}

function SiteLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef(null);
  const location = useLocation();
  const { isConfigured, user } = useAuth();

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) return undefined;

    function onKeyDown(event) {
      if (event.key === 'Escape') {
        setMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    }

    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [menuOpen]);

  const navLinks = [
    { to: '/services', label: 'Features' },
    { to: '/about', label: 'About' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/contact', label: 'Contact' },
  ];

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <PageMeta />
      <header className="site-header">
        <div className="header-inner page-width">
          <Link className="brand" to="/" aria-label="Orbitboard home">
            <OrbitMark />
            <span>orbitboard</span>
          </Link>
          <button
            ref={menuButtonRef}
            className="menu-toggle"
            type="button"
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="menu-toggle-icon" aria-hidden="true" />
            <span>{menuOpen ? 'Close menu' : 'Menu'}</span>
          </button>
          <nav
            className={`primary-navigation${menuOpen ? ' is-open' : ''}`}
            id="primary-navigation"
            aria-label="Primary navigation"
          >
            {navLinks.map((link) => (
              <NavLink
                to={link.to}
                key={link.to}
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </NavLink>
            ))}
            <Link className="nav-cta" to="/#preview" onClick={() => setMenuOpen(false)}>
              Explore sample <span aria-hidden="true">↗</span>
            </Link>
            <Link
              className="nav-account"
              to={isConfigured && user ? '/account' : '/login'}
              onClick={() => setMenuOpen(false)}
            >
              {isConfigured && user ? 'Your account' : 'Sign in'}
            </Link>
          </nav>
        </div>
      </header>
      <main id="main-content" tabIndex="-1">
        <Outlet />
      </main>
      <footer className="site-footer">
        <div className="footer-main page-width">
          <div className="footer-brand-block">
            <Link className="brand footer-brand" to="/">
              <OrbitMark />
              <span>orbitboard</span>
            </Link>
            <p>A considered view of what teams could plan together.</p>
            <span className="demo-label">PRODUCT PREVIEW · ACCOUNTS OPTIONAL</span>
          </div>
          <div className="footer-links">
            <div>
              <span className="footer-heading">Explore</span>
              <Link to="/services">Features</Link>
              <Link to="/about">About</Link>
              <Link to="/pricing">Pricing</Link>
            </div>
            <div>
              <span className="footer-heading">Information</span>
              <Link to="/contact">Contact</Link>
              <Link to="/privacy">Privacy</Link>
              <Link to="/terms">Terms</Link>
            </div>
          </div>
          <Link className="footer-sample-link" to="/#preview">
            View the sample roadmap <span aria-hidden="true">↗</span>
          </Link>
        </div>
        <div className="footer-bottom page-width">
          <span>© {new Date().getFullYear()} Orbitboard · Product preview</span>
          <span>Roadmap data and billing are not available in this preview.</span>
        </div>
      </footer>
    </>
  );
}

export default SiteLayout;
