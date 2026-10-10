import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppProviders from './lib/AppProviders';
import MotionCanvas from './components/common/MotionCanvas';
import CookieConsent from './components/common/CookieConsent';
import './lib/theme';
import { authFeature, dashboardFeature, profileFeature, paymentsFeature } from './features';


const Home = lazy(() => import('./pages/Home'));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Admin = lazy(() => import("./pages/Admin"));
const Checkout = lazy(() => import("./pages/Checkout"));
const About = lazy(() => import('./pages/About'));
const Services = lazy(() => import('./pages/Services'));
const Pricing = lazy(() => import('./pages/Pricing'));
const Contact = lazy(() => import('./pages/Contact'));
const Account = lazy(() => import('./pages/Account'));
const Listings = lazy(() => import('./pages/Listings'));
const Privacy = lazy(() => import('./pages/Privacy'));
const Terms = lazy(() => import('./pages/Terms'));

const NotFound = lazy(() => import('./pages/NotFound'));
function Loader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="skeleton-shimmer h-8 w-8 rounded-full" />
    </div>
  );
}

const basename = import.meta.env.BASE_URL || '/';

const featureRegistry = [authFeature, dashboardFeature, profileFeature, paymentsFeature];

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter basename={basename}>
        <MotionCanvas className="fixed inset-0 -z-10" />
        <CookieConsent />
        <div>
          <Suspense fallback={<Loader />}>
            <Routes>
              <Route path="/listings" element={<Listings />} />
              <Route path="/account" element={<Account />} />
              <Route path="/about" element={<About />} />
              <Route path="/services" element={<Services />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/checkout" element={<Checkout />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="/" element={<Home />} />
              
              <Route path="*" element={<NotFound />} />

              
            </Routes>
          </Suspense>
        </div>
      </BrowserRouter>
    </AppProviders>
  );
}
