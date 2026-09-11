import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sparkles, Zap } from 'lucide-react';
import { SkipToContent, BrandLogo, LicenseWatermark } from '../components/common';
import GlassNavbar from '../components/common/GlassNavbar';
import { Button } from '../components/ui';

export default function MainLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <SkipToContent />
      <GlassNavbar />
      <LicenseWatermark />

      <main id="main-content" role="main" aria-label="Main content" className="flex-1">
        <div key={location.pathname} className="container mx-auto px-4 py-8 animate-page-enter">
          <Outlet />
        </div>
      </main>

      <footer
        role="contentinfo"
        aria-label="Site footer"
        className="border-t border-border bg-card"
      >
        <div className="container mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div className="md:col-span-2">
              <BrandLogo variant="full" size="md" />
              <p className="text-sm text-muted-foreground max-w-md mt-4 leading-relaxed">
                {t('layout.footerTagline')}
              </p>
              <div className="flex items-center gap-2 mt-4">
                <Button variant="primary" leftIcon={Sparkles} onClick={() => navigate('/generate')}>
                  {t('layout.generateWebsite')}
                </Button>
              </div>
            </div>
            <div>
              <h3 className="font-display font-semibold mb-4">{t('layout.templatesTitle')}</h3>
              <ul className="space-y-2" role="list">
                {[
                  { path: '/templates', label: t('layout.allTemplates') },
                  { path: '/templates/dashboard/DashboardOverview', label: t('layout.dashboard') },
                  { path: '/templates/ecommerce/ProductListing', label: t('layout.eCommerce') },
                  { path: '/templates/ai/ChatInterface', label: t('layout.aiInterfaces') },
                  { path: '/templates/business/LandingPage', label: t('layout.business') },
                  { path: '/templates/restaurant/RestaurantMenu', label: t('layout.restaurant') },
                  { path: '/templates/realestate/PropertyListing', label: t('layout.realEstate') },
                  { path: '/templates/healthcare/MedicalPortal', label: t('layout.healthcare') },
                ].map((link) => (
                  <li key={link.path}>
                    <Link
                      to={link.path}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-display font-semibold mb-4">{t('layout.moreTitle')}</h3>
              <ul className="space-y-2" role="list">
                {[
                  { path: '/templates/fitness/GymLanding', label: t('layout.fitness') },
                  { path: '/templates/education/CourseCatalog', label: t('layout.education') },
                  { path: '/templates/travel/TravelAgency', label: t('layout.travel') },
                  { path: '/templates/portfolio/PersonalPortfolio', label: t('layout.portfolio') },
                  { path: '/templates/creative/CreativeStudio', label: t('layout.creative') },
                  { path: '/generate', label: t('layout.aiGenerator') },
                  { path: '/login', label: t('navigation.login') },
                  { path: '/register', label: t('navigation.register') },
                ].map((link) => (
                  <li key={link.path}>
                    <Link
                      to={link.path}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="border-t border-border pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted-foreground">
            <p>{t('layout.rights')}</p>
            <p className="flex items-center gap-1.5">
              <Zap className="h-3 w-3 text-primary" aria-hidden="true" />
              {t('layout.builtWith')}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
