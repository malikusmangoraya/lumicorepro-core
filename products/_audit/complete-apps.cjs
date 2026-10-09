/**
 * complete-apps.cjs — closes the completeness gaps found by the audit, in all 11 products:
 *
 *   1. a brand-aware 404 route (previously `path="*"` silently rendered the homepage),
 *   2. the shipped CookieConsent banner actually mounted (it existed but had zero importers),
 *   3. dangling <Route> elements removed and every route element verified against its lazy
 *      import — apex shipped `<Route path="/projects" element={<Projects />} />` with no
 *      `Projects` import and no page, which is a build breaker.
 *
 * Run: node products/_audit/complete-apps.cjs
 */
const fs = require('fs');

const PRODUCTS = [
  'apex',
  'aurelia-estates',
  'aurum-fitness',
  'claimflow-ai',
  'flowpilot',
  'meridian-capital',
  'nuage-events',
  'prestige-studio',
  'resupro',
  'saffron-voyage',
  'studio-lumen',
];

// Pages every product ships; anything else is the product's own signature page.
const COMMON_PAGES = new Set([
  'About',
  'Account',
  'Admin',
  'Checkout',
  'Contact',
  'Home',
  'Insights',
  'Login',
  'Pricing',
  'Privacy',
  'Register',
  'Services',
  'Terms',
  'Projects',
  'NotFound',
]);

const NOT_FOUND = (brand, signature) => `/**
 * 404 — rendered for any path that matches no route.
 *
 * Without this the catch-all route silently rendered the homepage, which hides broken
 * links from the user and reports a 200 to crawlers for a URL that does not exist.
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Compass, Home, LifeBuoy } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { BRAND } from '../components/brand/BRAND';

export default function NotFound() {
  const { t } = useTranslation();

  const destinations = [
    { to: '/', label: t('common.home', 'Home'), icon: Home },
    { to: '${signature.path}', label: t('common.${signature.key}', '${signature.label}'), icon: Compass },
    { to: '/contact', label: t('common.contact', 'Contact'), icon: LifeBuoy },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main id="main-content" className="flex-1 fluid-container py-16 sm:py-24">
        <section className="max-w-3xl">
        <p className="section-eyebrow">{BRAND.name}</p>
        <p
          className="text-[6rem] font-extrabold leading-none sm:text-[9rem]"
          style={{ color: 'var(--t-primary)' }}
          aria-hidden="true"
        >
          404
        </p>
        <h1 className="section-heading mt-2">
          {t('common.not_found_heading', 'This page could not be found')}
        </h1>
        <p className="mt-4 max-w-xl" style={{ color: 'var(--t-muted)' }}>
          {t(
            'common.not_found_body',
            'The link may be out of date, or the page may have moved. Everything else is still where you left it.'
          )}
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          {destinations.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to} className="btn-outline">
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </Link>
          ))}
          <button type="button" className="btn-primary" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t('common.go_back', 'Go back')}
          </button>
        </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
`;

/** The product's own signature route, or Home when it has none. */
function signatureDestination(id, pages) {
  const extra = pages.filter((name) => !COMMON_PAGES.has(name));
  if (!extra.length) return { path: '/services', label: 'Services', key: 'services' };
  const label = extra[0];
  return {
    path: `/${label.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase()}`,
    label,
    key: label.toLowerCase(),
  };
}

const report = [];
for (const id of PRODUCTS) {
  const src = `products/${id}/frontend/src`;
  const appPath = `${src}/App.jsx`;
  const pages = fs
    .readdirSync(`${src}/pages`)
    .filter((f) => f.endsWith('.jsx'))
    .map((f) => f.replace('.jsx', ''));
  const brandSrc = fs.readFileSync(`${src}/components/brand/BRAND.js`, 'utf8');
  const brand = (brandSrc.match(/name:\s*"([^"]*)"/) || [])[1] || id;

  const signature = signatureDestination(id, pages);
  const before = fs.readFileSync(appPath, 'utf8');
  let app = before;

  /* 1. The 404 page itself. */
  fs.writeFileSync(`${src}/pages/NotFound.jsx`, NOT_FOUND(brand, signature).replace(/\n/g, '\r\n'));

  /* 2. Lazy import for it, appended after the last page import, whatever quoting the
        product's generator used. */
  if (!/const NotFound = lazy/.test(app)) {
    const lazyLines = [...app.matchAll(/^const [A-Za-z0-9_]+ = lazy\(.*\);\s*$/gm)];
    const last = lazyLines[lazyLines.length - 1];
    if (last) {
      const insertAt = last.index + last[0].length;
      app = `${app.slice(0, insertAt)}\nconst NotFound = lazy(() => import('./pages/NotFound'));${app.slice(insertAt)}`;
    }
  }

  /* 3. The catch-all route now points at it. */
  if (/<Route path="\*" element=\{<Home \/>\} \/>/.test(app)) {
    app = app.replace(
      '<Route path="*" element={<Home />} />',
      '<Route path="*" element={<NotFound />} />'
    );
  } else if (!/<Route path="\*"/.test(app)) {
    // An earlier pass may have dropped the catch-all along with the dangling route.
    app = app.replace(
      /^(\s*)<\/Routes>/m,
      (_m, indent) => `${indent}  <Route path="*" element={<NotFound />} />\n${indent}</Routes>`
    );
  }

  /* 4. Drop routes whose element has no import and no page (the apex /projects breaker). */
  const dangling = [];
  for (const m of app.matchAll(/<Route path="([^"]+)" element=\{<([A-Za-z0-9_]+) \/>\} \/>/g)) {
    const [, routePath, element] = m;
    const imported = new RegExp(`const ${element} = lazy`).test(app);
    if (!imported) {
      dangling.push(`${routePath} → <${element} />`);
      app = app.replace(m[0], '');
    }
  }
  app = app.replace(/\n{3,}/g, '\n\n');

  /* 5. Mount cookie consent: it shipped in all 11 but nothing imported it. The banner is
        rendered once, just inside the router, so it is present on every route. */
  if (!/from '\.\/components\/common\/CookieConsent'/.test(app)) {
    app = app.replace(
      /^(import AppProviders from '\.\/lib\/AppProviders';\s*)$/m,
      (_m, line) => `${line}\nimport CookieConsent from './components/common/CookieConsent';`
    );
  }
  if (!/<CookieConsent \/>/.test(app)) {
    const close = app.match(/^(\s*)<\/BrowserRouter>/m);
    if (close) {
      const indent = `${close[1]}  `;
      app = app.replace(close[0], `${indent}<CookieConsent />\n${close[0]}`);
    } else {
      app = app.replace(/(^\s*)<\/AppProviders>/m, (_m, indent) => `${indent}  <CookieConsent />\n${_m}`);
    }
  }
  const consentMounted = /<CookieConsent \/>/.test(app);

  /* 6. Verify: every route element must resolve to a lazy import. */
  const unresolved = [];
  for (const m of app.matchAll(/<Route path="([^"]+)" element=\{<([A-Za-z0-9_]+) \/>\} \/>/g)) {
    if (!new RegExp(`const ${m[2]} = lazy`).test(app)) unresolved.push(m[2]);
  }
  const hasCatchAll = /<Route path="\*" element=\{<NotFound \/>\} \/>/.test(app);
  const importsNotFound = /const NotFound = lazy/.test(app);

  if (app !== before) fs.writeFileSync(appPath, app);

  report.push({
    id: id.padEnd(18),
    signature: `${signature.label} (${signature.path})`,
    danglingRemoved: dangling.length ? dangling.join(' ') : '-',
    consentMounted,
    catchAll404: hasCatchAll,
    notFoundPage: fs.existsSync(`${src}/pages/NotFound.jsx`),
    unresolvedRoutes: unresolved.length ? unresolved.join(',') : '-',
    ok: consentMounted && hasCatchAll && importsNotFound && unresolved.length === 0 && !dangling.length,
  });
}

console.log('product            | signature page        | 404 | consent | dangling removed | self-check');
console.log('-------------------|-----------------------|-----|---------|------------------|-----------');
for (const r of report) {
  console.log(
    `${r.id} | ${r.signature.padEnd(21)} | ${r.catchAll404 ? ' ok' : ' NO'} | ${r.consentMounted ? '  ok   ' : '  NO   '} | ${r.danglingRemoved.padEnd(16)} | ${r.unresolvedRoutes === '-' ? 'clean' : 'UNRESOLVED ' + r.unresolvedRoutes}`
  );
}
const failed = report.filter((r) => !r.ok);
console.log(`\n${report.length - failed.length}/${report.length} apps completed`);
if (failed.length) console.log('failed: ' + failed.map((r) => r.id.trim()).join(', '));
process.exitCode = failed.length ? 1 : 0;
