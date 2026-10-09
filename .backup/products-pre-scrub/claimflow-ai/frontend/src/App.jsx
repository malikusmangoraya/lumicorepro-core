import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppProviders from './lib/AppProviders';
import MotionCanvas from './components/common/MotionCanvas';
import './lib/theme';

const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import("./pages/About"));
const Services = lazy(() => import("./pages/Services"));
const Pricing = lazy(() => import("./pages/Pricing"));
const Privacy = lazy(() => import('./pages/Privacy'));
const Terms = lazy(() => import('./pages/Terms'));
const Contact = lazy(() => import("./pages/Contact"));

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="skeleton-shimmer h-8 w-8 rounded-full" />
    </div>
  );
}

const basename =
  typeof window !== 'undefined' && window.location.pathname.split('/')[1]
    ? '/' + window.location.pathname.split('/')[1]
    : '/';

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter basename={basename}>
        <MotionCanvas className="fixed inset-0 -z-10" />
        <div className="cls-reserve">
          <Suspense fallback={<Loader />}>
            <Routes>
              <Route path="/about" element={<About />} />
              <Route path="/services" element={<Services />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="/" element={<Home />} />
              <Route path="*" element={<Home />} />
            </Routes>
          </Suspense>
        </div>
      </BrowserRouter>
    </AppProviders>
  );
}
