import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  Sun,
  Moon,
  Home,
  Store,
  BarChart3,
  Brain,
  Briefcase,
  LogIn,
  LogOut,
  Menu,
  X,
  Settings,
  Bell,
  User,
  LayoutTemplate,
  Sparkles,
  Zap,
  Key,
} from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { useTheme } from './ThemeProvider';
import { BrandLogo, Language } from '../common';
import { CurrencySelector } from '../CurrencySelector';
import { cn } from '../../utils';
import { IconButton, Button, Dropdown, DropdownItem, DropdownDivider } from '../ui';

function navActive(pathname, item) {
  if (item.match === 'exact') return pathname === item.path;
  if (item.match === 'prefix')
    return pathname === item.path || pathname.startsWith(`${item.path}/`);
  return pathname === item.path;
}

const mobileMenuVariants = {
  hidden: { x: '-100%' },
  visible: { x: 0, transition: { type: 'spring', stiffness: 300, damping: 30 } },
  exit: { x: '-100%', transition: { duration: 0.2 } },
};

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
};

export default function GlassNavbar() {
  const { isAuthenticated, logout, language, setLanguage } = useAppContext();
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const isDark = theme === 'dark';

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const navItems = [
    { path: '/', label: t('navigation.home'), icon: Home, match: 'exact' },
    { path: '/templates', label: t('navigation.templates'), icon: LayoutTemplate, match: 'prefix' },
    {
      path: '/templates/dashboard/DashboardOverview',
      label: t('layout.dashboard'),
      icon: BarChart3,
      match: 'exact',
      group: '/templates/dashboard',
    },
    {
      path: '/templates/ecommerce/ProductListing',
      label: t('layout.shop'),
      icon: Store,
      match: 'exact',
      group: '/templates/ecommerce',
    },
    {
      path: '/templates/ai/ChatInterface',
      label: t('layout.ai'),
      icon: Brain,
      match: 'exact',
      group: '/templates/ai',
    },
    {
      path: '/templates/business/LandingPage',
      label: t('layout.business'),
      icon: Briefcase,
      match: 'exact',
      group: '/templates/business',
    },
    {
      path: '/generate',
      label: t('navigation.generate'),
      icon: Sparkles,
      match: 'exact',
      highlight: true,
    },
    {
      path: '/api-settings',
      label: t('navigation.apiSettings'),
      icon: Key,
      match: 'exact',
    },
  ];

  const isItemActive = (item) => {
    if (item.group && location.pathname.startsWith(item.group)) return true;
    return navActive(location.pathname, item);
  };

  const NavItem = ({ item, onNavigate }) => {
    const Icon = item.icon;
    const active = isItemActive(item);
    if (item.highlight) {
      return (
        <Button
          variant={active ? 'primary' : 'outline'}
          size="sm"
          leftIcon={Icon}
          onClick={() => {
            onNavigate?.();
            navigate(item.path);
          }}
          className={cn(
            'font-semibold',
            !active &&
              'bg-primary/10 text-primary border border-primary/30 hover:bg-primary hover:text-primary-foreground'
          )}
          aria-current={active ? 'page' : undefined}
        >
          {item.label}
        </Button>
      );
    }
    return (
      <motion.div whileHover={{ scale: 1.05 }} className="relative">
        <Link
          to={item.path}
          onClick={onNavigate}
          className={cn(
            'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
            active
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/70'
          )}
          aria-current={active ? 'page' : undefined}
        >
          <Icon className="h-4 w-4 shrink-0" strokeWidth={2} aria-hidden="true" />
          <span>{item.label}</span>
        </Link>
        {active && (
          <motion.div
            layoutId="nav-underline"
            className="absolute -bottom-1 left-3 right-3 h-0.5 bg-primary rounded-full"
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          />
        )}
      </motion.div>
    );
  };

  const accountTrigger = (
    <Button
      variant="ghost"
      size="sm"
      leftIcon={User}
      rightIcon={ChevronDown}
      className="inline-flex items-center gap-2 px-2.5 py-1.5 hover:bg-accent"
      aria-label={t('layout.accountMenu')}
    >
      <span className="font-medium">{t('layout.account')}</span>
    </Button>
  );

  return (
    <header
      role="banner"
      aria-label="Site header"
      className="sticky top-0 z-50 w-full border-b border-border backdrop-blur-md bg-white/70 dark:bg-slate-900/70 supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-slate-900/60"
    >
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between gap-4">
          <div className="flex items-center gap-6 min-w-0">
            <BrandLogo variant="full" size="md" />
            <nav
              role="navigation"
              aria-label="Main navigation"
              className="hidden lg:flex items-center gap-0.5"
            >
              {navItems.map((item) => (
                <NavItem key={item.path} item={item} />
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <span className="hidden md:inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary">
              <Zap className="h-3 w-3" aria-hidden="true" />
              {t('layout.templatesBadge')}
            </span>

            <Language currentLang={language || 'en'} onLanguageChange={setLanguage} />
            <CurrencySelector />

            <IconButton
              icon={isDark ? Sun : Moon}
              label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              onClick={toggleTheme}
              variant="ghost"
              size="md"
            />

            {isAuthenticated ? (
              <div className="hidden md:block">
                <Dropdown
                  trigger={accountTrigger}
                  align="right"
                  animate="scale"
                  menuClassName="w-52"
                >
                  <DropdownItem icon={User} onClick={() => navigate('/profile')}>
                    {t('navigation.profile')}
                  </DropdownItem>
                  <DropdownItem icon={Settings} onClick={() => navigate('/settings')}>
                    {t('navigation.settings')}
                  </DropdownItem>
                  <DropdownItem icon={Bell}>{t('layout.notifications')}</DropdownItem>
                  <DropdownDivider />
                  <DropdownItem icon={LogOut} danger onClick={() => logout()}>
                    {t('navigation.logout')}
                  </DropdownItem>
                </Dropdown>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  leftIcon={LogIn}
                  onClick={() => navigate('/login')}
                  className="text-muted-foreground hover:text-foreground"
                >
                  {t('navigation.login')}
                </Button>
                <Button variant="primary" size="sm" onClick={() => navigate('/register')}>
                  {t('navigation.register')}
                </Button>
              </div>
            )}

            <IconButton
              icon={mobileMenuOpen ? X : Menu}
              label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden"
              size="md"
              aria-expanded={mobileMenuOpen}
            />
          </div>
        </div>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="lg:hidden"
          >
            <div
              className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
              aria-hidden="true"
            />
            <motion.div
              variants={mobileMenuVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              role="dialog"
              aria-label="Mobile navigation"
              className="fixed inset-y-0 left-0 z-50 w-72 bg-background border-r border-border shadow-xl flex flex-col"
            >
              <div className="flex items-center justify-between p-4 border-b border-border">
                <BrandLogo variant="full" size="sm" onClick={() => setMobileMenuOpen(false)} />
                <IconButton
                  icon={X}
                  label="Close menu"
                  size="sm"
                  onClick={() => setMobileMenuOpen(false)}
                />
              </div>
              <nav
                role="navigation"
                aria-label="Mobile navigation"
                className="flex-1 p-3 space-y-1 overflow-y-auto"
              >
                {navItems.map((item) => (
                  <NavItem
                    key={item.path}
                    item={item}
                    onNavigate={() => setMobileMenuOpen(false)}
                  />
                ))}
                <div className="pt-2 border-t border-border mt-2">
                  <p className="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {t('layout.moreTemplates')}
                  </p>
                  {[
                    {
                      path: '/templates/restaurant/RestaurantMenu',
                      label: t('layout.restaurant'),
                      icon: Store,
                    },
                    {
                      path: '/templates/realestate/PropertyListing',
                      label: t('layout.realEstate'),
                      icon: Home,
                    },
                    {
                      path: '/templates/healthcare/MedicalPortal',
                      label: t('layout.healthcare'),
                      icon: Brain,
                    },
                    {
                      path: '/templates/fitness/GymLanding',
                      label: t('layout.fitness'),
                      icon: Zap,
                    },
                    {
                      path: '/templates/education/CourseCatalog',
                      label: t('layout.education'),
                      icon: Briefcase,
                    },
                    {
                      path: '/templates/travel/TravelAgency',
                      label: t('layout.travel'),
                      icon: LayoutTemplate,
                    },
                    {
                      path: '/templates/portfolio/PersonalPortfolio',
                      label: t('layout.portfolio'),
                      icon: User,
                    },
                    {
                      path: '/templates/creative/CreativeStudio',
                      label: t('layout.creative'),
                      icon: Sparkles,
                    },
                  ].map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              </nav>
              <div className="border-t border-border p-4 space-y-2">
                {isAuthenticated ? (
                  <Button
                    variant="ghost"
                    size="md"
                    leftIcon={LogOut}
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    className="w-full text-destructive hover:bg-destructive/10"
                  >
                    {t('navigation.logout')}
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      size="md"
                      fullWidth
                      leftIcon={LogIn}
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate('/login');
                      }}
                    >
                      {t('navigation.login')}
                    </Button>
                    <Button
                      variant="primary"
                      size="md"
                      fullWidth
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate('/register');
                      }}
                    >
                      {t('layout.createAccount')}
                    </Button>
                  </>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
