import React from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import { requireAuth } from './auth.js';
import GlassNavbar from './components/common/GlassNavbar.jsx';
import ModernFooter from './components/common/ModernFooter.jsx';
import Home from './pages/Home.jsx';
import Features from './pages/Features.jsx';
import Pricing from './pages/Pricing.jsx';
import About from './pages/About.jsx';
import Contact from './pages/Contact.jsx';
import Privacy from './pages/Privacy.jsx';
import Terms from './pages/Terms.jsx';
import NotFound from './pages/NotFound.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Generator from './pages/Generator.jsx';
import History from './pages/History.jsx';
import Credits from './pages/Credits.jsx';
import WorkspaceLayout from './layouts/WorkspaceLayout.jsx';
import ToastProvider from './components/common/Toast.jsx';
import CookieConsent from './components/common/CookieConsent.jsx';
import { translate, useLocale } from './i18n.js';

function AppRoutes() {
  const location = useLocation();
  const locale = useLocale();
  const isAuthRoute = /^\/(?:login|register)\/?$/.test(location.pathname);
  if (location.pathname.startsWith('/generate')) {
    requireAuth();
    return (
      <Routes>
        <Route path="/generate" element={<WorkspaceLayout />}>
          <Route index element={<Generator />} />
          <Route path="history" element={<History />} />
          <Route path="credits" element={<Credits />} />
        </Route>
      </Routes>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden">
      <a href="#main-content" className="skip-link">{translate(locale, 'skip')}</a>
      {!isAuthRoute && <div role="status" className="bg-brand-primary/15 border-b border-brand-primary/30 px-4 py-2 text-center text-sm text-slate-200">{translate(locale, 'evaluationBanner')}</div>}
      {!isAuthRoute && <GlassNavbar brand="BlogForge" />}
      <main id="main-content" className="flex-1" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/features" element={<Features />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      {!isAuthRoute && <ModernFooter brand="BlogForge" />}
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <CookieConsent />
      <AppRoutes />
    </ToastProvider>
  );
}
