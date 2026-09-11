import { useNavigate } from 'react-router-dom';
import { Home, Sparkles, Search } from 'lucide-react';
import { Button, Card } from '@/components/ui';
import PageSEO from '@/components/common/PageSEO';

const QUICK_LINKS = [
  { path: '/templates', label: '60 Templates', icon: '🎨' },
  { path: '/generate', label: 'AI Generator', icon: '⚡' },
  { path: '/templates/restaurant/RestaurantMenu', label: 'Restaurant', icon: '🍽️' },
  { path: '/templates/realestate/PropertyListing', label: 'Real Estate', icon: '🏠' },
  { path: '/templates/healthcare/MedicalPortal', label: 'Healthcare', icon: '🏥' },
];

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background -mx-4 -my-8 px-4">
      <PageSEO title="Page Not Found — LumicorePro" description="The page you are looking for does not exist." noIndex />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.06),transparent_60%)]" />

      <div className="relative text-center max-w-lg w-full animate-fade-in-up">
        <div className="relative inline-block mb-6">
          <span className="font-display text-[10rem] font-black text-primary/10 leading-none select-none">
            404
          </span>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-24 w-24 rounded-3xl bg-primary/15 border border-primary/30 flex items-center justify-center animate-glow-pulse">
              <Search className="h-10 w-10 text-primary" />
            </div>
          </div>
        </div>

        <h1 className="font-display text-3xl font-bold mb-3">Page not found</h1>
        <p className="text-muted-foreground mb-8 leading-relaxed">
          The page you're looking for doesn't exist or has been moved. Try one of the links below.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-10">
          <Button variant="primary" size="lg" leftIcon={Home} onClick={() => navigate('/')}>
            Back to Home
          </Button>
          <Button
            variant="outline"
            size="lg"
            leftIcon={Sparkles}
            onClick={() => navigate('/templates')}
          >
            Browse Templates
          </Button>
        </div>

        <Card animate="fade-up" className="p-6">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            Popular Pages
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {QUICK_LINKS.map((link) => (
              <Button
                key={link.path}
                variant="ghost"
                size="sm"
                className="justify-start border border-border/60 bg-background/60"
                onClick={() => navigate(link.path)}
              >
                <span className="text-base">{link.icon}</span>
                <span className="text-xs font-medium truncate">{link.label}</span>
              </Button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
