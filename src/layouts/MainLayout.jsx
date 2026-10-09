import { Outlet, useLocation } from 'react-router-dom';
import SkipToContent from '../components/common/SkipToContent';
import LicenseWatermark from '../components/common/LicenseWatermark';
import ModernFooter from '../components/common/ModernFooter';
import GlassNavbar from '../components/common/GlassNavbar';
import ScrollProgress from '../components/ui/ScrollProgress';
import BackToTop from '../components/ui/BackToTop';
import useCartServerSync from '../hooks/useCartServerSync';

export default function MainLayout() {
  const location = useLocation();
  // Keeps the Zustand cart in step with the account cart (no-op when logged out).
  useCartServerSync();

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

      <ModernFooter brandName="LumicorePro" />
      <BackToTop />
    </div>
  );
}
