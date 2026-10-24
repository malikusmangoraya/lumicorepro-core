import { Suspense, lazy } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import SkipToContent from '../components/common/SkipToContent';
import LicenseWatermark from '../components/common/LicenseWatermark';
import GlassNavbar from '../components/common/GlassNavbar';
import ScrollProgress from '../components/ui/ScrollProgress';
import AuthLayout from './AuthLayout';
import BackToTop from '../components/ui/BackToTop';
import useCartServerSync from '../hooks/useCartServerSync';

// Below-the-fold: defer off the critical path (bundle budget has ~0 headroom).
const ModernFooter = lazy(() => import('../components/common/ModernFooter'));

export default function MainLayout() {
  const location = useLocation();
  // Keeps the Zustand cart in step with the account cart (no-op when logged out).
  useCartServerSync();

  const isAuthRoute = /^\/(?:login|register|forgot-password|reset-password(?:\/|$)|verify-email(?:\/|$))\/?$/.test(
    location.pathname
  );

  if (isAuthRoute) {
    return <AuthLayout />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/20 selection:text-primary">
      <SkipToContent />
      <ScrollProgress />
      <GlassNavbar />
      <LicenseWatermark />

      <main
        id="main-content"
        role="main"
        aria-label="Main content"
        className="flex-1 min-h-[100svh]"
      >
        <div key={location.pathname} className="container mx-auto px-4 py-8 animate-page-enter">
          <Outlet />
        </div>
      </main>

      <Suspense fallback={null}>
        <ModernFooter brandName="LumicorePro" />
      </Suspense>
      <BackToTop />
    </div>
  );
}
