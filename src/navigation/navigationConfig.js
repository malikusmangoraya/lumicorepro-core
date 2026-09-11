/**
 * Navigation Configuration
 * Defines full hierarchy of navigation links for Navbar, Sidebar, Dashboard, Templates, and Footer.
 */

export const mainNavLinks = [
  {
    label: 'Home',
    href: '/',
    icon: 'Home',
  },
  {
    label: 'Templates',
    href: '/templates',
    icon: 'LayoutGrid',
    badge: '60+',
  },
  {
    label: 'AI Generator',
    href: '/generate',
    icon: 'Sparkles',
    highlight: true,
  },
  {
    label: 'AI Chat',
    href: '/chat',
    icon: 'MessageSquare',
  },
  {
    label: 'Pricing',
    href: '/pricing',
    icon: 'CreditCard',
  },
  {
    label: 'Store',
    href: '/templates/ecommerce/ProductListing',
    icon: 'ShoppingBag',
  },
  {
    label: 'Dashboard',
    href: '/templates/dashboard/DashboardOverview',
    icon: 'BarChart3',
    roles: ['admin', 'vendor', 'user'],
  },
  {
    label: 'API Settings',
    href: '/api-settings',
    icon: 'Key',
  },
];

export const dashboardNavLinks = [
  {
    group: 'Core',
    items: [
      {
        label: 'Overview',
        href: '/templates/dashboard/DashboardOverview',
        icon: 'LayoutDashboard',
      },
      {
        label: 'Analytics',
        href: '/templates/dashboard/Analytics',
        icon: 'TrendingUp',
      },
      {
        label: 'Users Management',
        href: '/templates/dashboard/UsersManagement',
        icon: 'Users',
        roles: ['admin'],
      },
      {
        label: 'Global System Settings',
        href: '/admin/settings',
        icon: 'Settings2',
        roles: ['admin'],
      },
    ],
  },
  {
    group: 'E-Commerce',
    items: [
      {
        label: 'Products Catalog',
        href: '/templates/ecommerce/ProductListing',
        icon: 'Package',
      },
      {
        label: 'Orders History',
        href: '/templates/ecommerce/OrdersHistory',
        icon: 'ShoppingBag',
      },
      {
        label: 'Shopping Cart',
        href: '/templates/ecommerce/ShoppingCart',
        icon: 'ShoppingCart',
      },
    ],
  },
  {
    group: 'AI Studio',
    items: [
      {
        label: 'AI Chat',
        href: '/templates/ai/ChatInterface',
        icon: 'MessageSquare',
      },
      {
        label: 'AI Generator',
        href: '/templates/ai/AIGenerator',
        icon: 'Wand2',
      },
      {
        label: 'Model Selection',
        href: '/templates/ai/ModelSelection',
        icon: 'Cpu',
      },
      {
        label: 'Usage Dashboard',
        href: '/templates/ai/UsageDashboard',
        icon: 'Gauge',
      },
      {
        label: 'Generation History',
        href: '/templates/ai/GenerationHistory',
        icon: 'History',
      },
    ],
  },
  {
    group: 'Account',
    items: [
      {
        label: 'Profile',
        href: '/templates/dashboard/Profile',
        icon: 'User',
      },
      {
        label: 'Settings',
        href: '/templates/dashboard/Settings',
        icon: 'Settings',
      },
    ],
  },
];

export const templateCategories = [
  {
    category: 'Dashboard & Admin',
    items: [
      { label: 'Dashboard Overview', href: '/templates/dashboard/DashboardOverview' },
      { label: 'Users Management', href: '/templates/dashboard/UsersManagement' },
      { label: 'Analytics', href: '/templates/dashboard/Analytics' },
      { label: 'Settings', href: '/templates/dashboard/Settings' },
      { label: 'Profile', href: '/templates/dashboard/Profile' },
    ],
  },
  {
    category: 'E-Commerce',
    items: [
      { label: 'Product Listing', href: '/templates/ecommerce/ProductListing' },
      { label: 'Product Details', href: '/templates/ecommerce/ProductDetails' },
      { label: 'Shopping Cart', href: '/templates/ecommerce/ShoppingCart' },
      { label: 'Checkout', href: '/templates/ecommerce/Checkout' },
      { label: 'Orders History', href: '/templates/ecommerce/OrdersHistory' },
    ],
  },
  {
    category: 'AI & Machine Learning',
    items: [
      { label: 'Chat Interface', href: '/templates/ai/ChatInterface' },
      { label: 'AI Generator', href: '/templates/ai/AIGenerator' },
      { label: 'Usage Dashboard', href: '/templates/ai/UsageDashboard' },
      { label: 'Model Selection', href: '/templates/ai/ModelSelection' },
      { label: 'Generation History', href: '/templates/ai/GenerationHistory' },
    ],
  },
  {
    category: 'Business & Agency',
    items: [
      { label: 'Landing Page', href: '/templates/business/LandingPage' },
      { label: 'Services Page', href: '/templates/business/ServicesPage' },
      { label: 'Portfolio Page', href: '/templates/business/PortfolioPage' },
      { label: 'Pricing Page', href: '/templates/business/PricingPage' },
      { label: 'Contact Page', href: '/templates/business/ContactPage' },
    ],
  },
  {
    category: 'Industry Specific',
    items: [
      { label: 'Restaurant Menu', href: '/templates/restaurant/RestaurantMenu' },
      { label: 'Real Estate Property', href: '/templates/realestate/PropertyListing' },
      { label: 'Healthcare Medical Portal', href: '/templates/healthcare/MedicalPortal' },
      { label: 'Fitness Gym Landing', href: '/templates/fitness/GymLanding' },
      { label: 'Education Course Catalog', href: '/templates/education/CourseCatalog' },
      { label: 'Travel Agency', href: '/templates/travel/TravelAgency' },
      { label: 'Personal Portfolio', href: '/templates/portfolio/PersonalPortfolio' },
      { label: 'Creative Studio', href: '/templates/creative/CreativeStudio' },
    ],
  },
];

export const userDropdownNav = [
  {
    label: 'My Profile',
    href: '/templates/dashboard/Profile',
    icon: 'User',
  },
  {
    label: 'Orders',
    href: '/templates/ecommerce/OrdersHistory',
    icon: 'ShoppingBag',
  },
  {
    label: 'Dashboard',
    href: '/templates/dashboard/DashboardOverview',
    icon: 'BarChart3',
  },
  {
    label: 'Settings',
    href: '/templates/dashboard/Settings',
    icon: 'Settings',
  },
];

export const footerNav = {
  solutions: [
    { label: 'AI Agent Generator', href: '/generate' },
    { label: 'E-Commerce Platform', href: '/templates/ecommerce/ProductListing' },
    { label: 'Admin Analytics', href: '/templates/dashboard/Analytics' },
    { label: 'Template Hub', href: '/templates' },
  ],
  support: [
    { label: 'Documentation', href: '/api-docs' },
    { label: 'API Reference', href: '/api-docs' },
    { label: 'API Settings', href: '/api-settings' },
    { label: 'Contact Us', href: '/templates/business/ContactPage' },
    { label: 'System Health', href: '/api/health' },
  ],
  company: [
    { label: 'About Us', href: '/templates/business/LandingPage' },
    { label: 'Services', href: '/templates/business/ServicesPage' },
    { label: 'Portfolio', href: '/templates/business/PortfolioPage' },
    { label: 'Pricing Plans', href: '/templates/business/PricingPage' },
  ],
};
