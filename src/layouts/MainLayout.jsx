import { Outlet, useLocation } from 'react-router-dom';
import { SkipToContent, LicenseWatermark, ModernFooter } from '../components/common';
import GlassNavbar from '../components/common/GlassNavbar';

export default function MainLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/20 selection:text-primary">
      <SkipToContent />
      <GlassNavbar />
      <LicenseWatermark />

      <main id="main-content" role="main" aria-label="Main content" className="flex-1">
        <div key={location.pathname} className="container mx-auto px-4 py-8 animate-page-enter">
          <Outlet />
        </div>
      </main>

      <ModernFooter brandName="LumicorePro" />
    </div>
  );
}
