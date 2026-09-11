/**
 * LumicorePro Router — full lazy-loading strategy
 * Every template is loaded only when its route is visited.
 * Core pages (Home, Templates, Generate) are eager — they're the entry points.
 * All 60 template pages are lazy — Suspense shows a skeleton while they load.
 * Each template group is wrapped in ErrorBoundary for graceful error recovery.
 */
import { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import ErrorBoundary from '../components/common/ErrorBoundary';
import SetupGate from '../components/gates/SetupGate';

// ── Eager pages (loaded immediately — small & critical) ───────────────────
import Home from '../pages/Home';
import TemplatesHub from '../pages/Templates';
import GeneratePage from '../pages/Generate';
import ApiSettings from '../pages/ApiSettings';
import NotFound from '../pages/NotFound';

const ChatPage = lazy(() => import('../pages/Chat'));
const PlanPricingPage = lazy(() => import('../pages/Pricing'));
const BillingPage = lazy(() => import('../pages/Billing'));
const GalleryPage = lazy(() => import('../pages/Gallery'));

const LoginPage = lazy(() => import('../pages/Login'));
const RegisterPage = lazy(() => import('../pages/Register'));
const SetupWizardPage = lazy(() => import('../pages/SetupWizard'));
const GlobalSystemSettingsPage = lazy(() => import('../pages/GlobalSystemSettings'));
const PrivacyPolicyPage = lazy(() => import('../pages/PrivacyPolicy'));
const TermsOfServicePage = lazy(() => import('../pages/TermsOfService'));
const RefundPolicyPage = lazy(() => import('../pages/RefundPolicy'));
const MarketingLandingPage = lazy(() => import('../pages/MarketingLanding'));
const ForgotPasswordPage = lazy(() => import('../pages/ForgotPassword'));
const ResetPasswordPage = lazy(() => import('../pages/ResetPassword'));
const VerifyEmailPage = lazy(() => import('../pages/VerifyEmail'));
const ChangePasswordPage = lazy(() => import('../pages/ChangePassword'));
const OAuthCallbackPage = lazy(() => import('../pages/OAuthCallback'));
const OrganizationsPage = lazy(() => import('../pages/Organizations'));
const OrganizationSettingsPage = lazy(() => import('../pages/OrganizationSettings'));

// ── Lazy template imports — each group is a separate chunk ────────────────
// Dashboard
const DashboardOverview = lazy(() => import('../templates/dashboard/DashboardOverview'));
const UsersManagement = lazy(() => import('../templates/dashboard/UsersManagement'));
const Analytics = lazy(() => import('../templates/dashboard/Analytics'));
const Settings = lazy(() => import('../templates/dashboard/Settings'));
const Profile = lazy(() => import('../templates/dashboard/Profile'));

// E-Commerce
const ProductListing = lazy(() => import('../templates/ecommerce/ProductListing'));
const ProductDetails = lazy(() => import('../templates/ecommerce/ProductDetails'));
const ShoppingCart = lazy(() => import('../templates/ecommerce/ShoppingCart'));
const Checkout = lazy(() => import('../templates/ecommerce/Checkout'));
const OrdersHistory = lazy(() => import('../templates/ecommerce/OrdersHistory'));

// AI
const ChatInterface = lazy(() => import('../templates/ai/ChatInterface'));
const AIGenerator = lazy(() => import('../templates/ai/AIGenerator'));
const UsageDashboard = lazy(() => import('../templates/ai/UsageDashboard'));
const ModelSelection = lazy(() => import('../templates/ai/ModelSelection'));
const GenerationHistory = lazy(() => import('../templates/ai/GenerationHistory'));

// Business
const LandingPage = lazy(() => import('../templates/business/LandingPage'));
const ServicesPage = lazy(() => import('../templates/business/ServicesPage'));
const PortfolioPage = lazy(() => import('../templates/business/PortfolioPage'));
const PricingPage = lazy(() => import('../templates/business/PricingPage'));
const ContactPage = lazy(() => import('../templates/business/ContactPage'));

// New industry templates
const RestaurantMenu = lazy(() => import('../templates/restaurant/RestaurantMenu'));
const ReservationSystem = lazy(() => import('../templates/restaurant/ReservationSystem'));
const OnlineOrders = lazy(() => import('../templates/restaurant/OnlineOrders'));
const ChefMenu = lazy(() => import('../templates/restaurant/ChefMenu'));
const RestaurantEvents = lazy(() => import('../templates/restaurant/RestaurantEvents'));

const PropertyListing = lazy(() => import('../templates/realestate/PropertyListing'));
const PropertyDetails = lazy(() => import('../templates/realestate/PropertyDetails'));
const AgentDirectory = lazy(() => import('../templates/realestate/AgentDirectory'));
const MortgageCalculator = lazy(() => import('../templates/realestate/MortgageCalculator'));
const CompareProperties = lazy(() => import('../templates/realestate/CompareProperties'));

const MedicalPortal = lazy(() => import('../templates/healthcare/MedicalPortal'));
const AppointmentBooking = lazy(() => import('../templates/healthcare/AppointmentBooking'));
const DoctorDirectory = lazy(() => import('../templates/healthcare/DoctorDirectory'));
const PatientDashboard = lazy(() => import('../templates/healthcare/PatientDashboard'));
const TelehealthRoom = lazy(() => import('../templates/healthcare/TelehealthRoom'));

const GymLanding = lazy(() => import('../templates/fitness/GymLanding'));
const ClassSchedule = lazy(() => import('../templates/fitness/ClassSchedule'));
const TrainerProfiles = lazy(() => import('../templates/fitness/TrainerProfiles'));
const MembershipPlans = lazy(() => import('../templates/fitness/MembershipPlans'));
const NutritionPlans = lazy(() => import('../templates/fitness/NutritionPlans'));

const CourseCatalog = lazy(() => import('../templates/education/CourseCatalog'));
const CourseDetails = lazy(() => import('../templates/education/CourseDetails'));
const InstructorDirectory = lazy(() => import('../templates/education/InstructorDirectory'));
const StudentDashboard = lazy(() => import('../templates/education/StudentDashboard'));
const CareerResources = lazy(() => import('../templates/education/CareerResources'));

const TravelAgency = lazy(() => import('../templates/travel/TravelAgency'));
const HotelBooking = lazy(() => import('../templates/travel/HotelBooking'));
const FlightSearch = lazy(() => import('../templates/travel/FlightSearch'));
const TourPackages = lazy(() => import('../templates/travel/TourPackages'));
const TravelBlog = lazy(() => import('../templates/travel/TravelBlog'));

const PersonalPortfolio = lazy(() => import('../templates/portfolio/PersonalPortfolio'));
const ProjectShowcase = lazy(() => import('../templates/portfolio/ProjectShowcase'));
const ResumeTimeline = lazy(() => import('../templates/portfolio/ResumeTimeline'));
const ServicesOffering = lazy(() => import('../templates/portfolio/ServicesOffering'));
const ContactMe = lazy(() => import('../templates/portfolio/ContactMe'));

const CreativeStudio = lazy(() => import('../templates/creative/CreativeStudio'));
const WorksGallery = lazy(() => import('../templates/creative/WorksGallery'));
const ServicesList = lazy(() => import('../templates/creative/ServicesList'));
const TeamCulture = lazy(() => import('../templates/creative/TeamCulture'));
const GetInTouch = lazy(() => import('../templates/creative/GetInTouch'));

// ── Shared loading skeleton shown while lazy chunks download ──────────────
function PageSkeleton() {
  return (
    <div className="animate-pulse space-y-4 py-8">
      <div className="h-8 bg-muted rounded-xl w-1/3" />
      <div className="h-4 bg-muted rounded-lg w-2/3" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-48 bg-muted rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

// ── Wrap lazy element in Suspense + ErrorBoundary ─────────────────────────
function L({ component: Component }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<PageSkeleton />}>
        <Component />
      </Suspense>
    </ErrorBoundary>
  );
}

// ── Template routes — all lazy ────────────────────────────────────────────
const templateRoutes = [
  { path: 'templates/dashboard/DashboardOverview', element: <L component={DashboardOverview} /> },
  { path: 'templates/dashboard/UsersManagement', element: <L component={UsersManagement} /> },
  { path: 'templates/dashboard/Analytics', element: <L component={Analytics} /> },
  { path: 'templates/dashboard/Settings', element: <L component={Settings} /> },
  { path: 'templates/dashboard/Profile', element: <L component={Profile} /> },

  { path: 'templates/ecommerce/ProductListing', element: <L component={ProductListing} /> },
  { path: 'templates/ecommerce/ProductDetails', element: <L component={ProductDetails} /> },
  { path: 'templates/ecommerce/ShoppingCart', element: <L component={ShoppingCart} /> },
  { path: 'templates/ecommerce/Checkout', element: <L component={Checkout} /> },
  { path: 'templates/ecommerce/OrdersHistory', element: <L component={OrdersHistory} /> },

  { path: 'templates/ai/ChatInterface', element: <L component={ChatInterface} /> },
  { path: 'templates/ai/AIGenerator', element: <L component={AIGenerator} /> },
  { path: 'templates/ai/UsageDashboard', element: <L component={UsageDashboard} /> },
  { path: 'templates/ai/ModelSelection', element: <L component={ModelSelection} /> },
  { path: 'templates/ai/GenerationHistory', element: <L component={GenerationHistory} /> },

  { path: 'templates/business/LandingPage', element: <L component={LandingPage} /> },
  { path: 'templates/business/ServicesPage', element: <L component={ServicesPage} /> },
  { path: 'templates/business/PortfolioPage', element: <L component={PortfolioPage} /> },
  { path: 'templates/business/PricingPage', element: <L component={PricingPage} /> },
  { path: 'templates/business/ContactPage', element: <L component={ContactPage} /> },

  { path: 'templates/restaurant/RestaurantMenu', element: <L component={RestaurantMenu} /> },
  { path: 'templates/restaurant/ReservationSystem', element: <L component={ReservationSystem} /> },
  { path: 'templates/restaurant/OnlineOrders', element: <L component={OnlineOrders} /> },
  { path: 'templates/restaurant/ChefMenu', element: <L component={ChefMenu} /> },
  { path: 'templates/restaurant/RestaurantEvents', element: <L component={RestaurantEvents} /> },

  { path: 'templates/realestate/PropertyListing', element: <L component={PropertyListing} /> },
  { path: 'templates/realestate/PropertyDetails', element: <L component={PropertyDetails} /> },
  { path: 'templates/realestate/AgentDirectory', element: <L component={AgentDirectory} /> },
  {
    path: 'templates/realestate/MortgageCalculator',
    element: <L component={MortgageCalculator} />,
  },
  { path: 'templates/realestate/CompareProperties', element: <L component={CompareProperties} /> },

  { path: 'templates/healthcare/MedicalPortal', element: <L component={MedicalPortal} /> },
  {
    path: 'templates/healthcare/AppointmentBooking',
    element: <L component={AppointmentBooking} />,
  },
  { path: 'templates/healthcare/DoctorDirectory', element: <L component={DoctorDirectory} /> },
  { path: 'templates/healthcare/PatientDashboard', element: <L component={PatientDashboard} /> },
  { path: 'templates/healthcare/TelehealthRoom', element: <L component={TelehealthRoom} /> },

  { path: 'templates/fitness/GymLanding', element: <L component={GymLanding} /> },
  { path: 'templates/fitness/ClassSchedule', element: <L component={ClassSchedule} /> },
  { path: 'templates/fitness/TrainerProfiles', element: <L component={TrainerProfiles} /> },
  { path: 'templates/fitness/MembershipPlans', element: <L component={MembershipPlans} /> },
  { path: 'templates/fitness/NutritionPlans', element: <L component={NutritionPlans} /> },

  { path: 'templates/education/CourseCatalog', element: <L component={CourseCatalog} /> },
  { path: 'templates/education/CourseDetails', element: <L component={CourseDetails} /> },
  {
    path: 'templates/education/InstructorDirectory',
    element: <L component={InstructorDirectory} />,
  },
  { path: 'templates/education/StudentDashboard', element: <L component={StudentDashboard} /> },
  { path: 'templates/education/CareerResources', element: <L component={CareerResources} /> },

  { path: 'templates/travel/TravelAgency', element: <L component={TravelAgency} /> },
  { path: 'templates/travel/HotelBooking', element: <L component={HotelBooking} /> },
  { path: 'templates/travel/FlightSearch', element: <L component={FlightSearch} /> },
  { path: 'templates/travel/TourPackages', element: <L component={TourPackages} /> },
  { path: 'templates/travel/TravelBlog', element: <L component={TravelBlog} /> },

  { path: 'templates/portfolio/PersonalPortfolio', element: <L component={PersonalPortfolio} /> },
  { path: 'templates/portfolio/ProjectShowcase', element: <L component={ProjectShowcase} /> },
  { path: 'templates/portfolio/ResumeTimeline', element: <L component={ResumeTimeline} /> },
  { path: 'templates/portfolio/ServicesOffering', element: <L component={ServicesOffering} /> },
  { path: 'templates/portfolio/ContactMe', element: <L component={ContactMe} /> },

  { path: 'templates/creative/CreativeStudio', element: <L component={CreativeStudio} /> },
  { path: 'templates/creative/WorksGallery', element: <L component={WorksGallery} /> },
  { path: 'templates/creative/ServicesList', element: <L component={ServicesList} /> },
  { path: 'templates/creative/TeamCulture', element: <L component={TeamCulture} /> },
  { path: 'templates/creative/GetInTouch', element: <L component={GetInTouch} /> },
];

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <SetupGate>
        <MainLayout />
      </SetupGate>
    ),
    errorElement: <ErrorBoundary />,
    children: [
      { index: true, element: <Home /> },
      {
        path: 'marketing',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <MarketingLandingPage />
          </Suspense>
        ),
      },
      { path: 'templates', element: <TemplatesHub /> },
      { path: 'generate', element: <GeneratePage /> },
      {
        path: 'chat',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <ChatPage />
          </Suspense>
        ),
      },
      {
        path: 'pricing',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <PlanPricingPage />
          </Suspense>
        ),
      },
      {
        path: 'billing',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <BillingPage />
          </Suspense>
        ),
      },
      {
        path: 'login',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <LoginPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'register',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <RegisterPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'setup',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <SetupWizardPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'admin/settings',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <GlobalSystemSettingsPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'forgot-password',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <ForgotPasswordPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'reset-password/:token',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <ResetPasswordPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'verify-email/:token',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <VerifyEmailPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'change-password',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <ChangePasswordPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'oauth/callback',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <OAuthCallbackPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />,
      },
      {
        path: 'api-settings',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <ApiSettings />
          </Suspense>
        ),
      },
      {
        path: 'gallery',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <GalleryPage />
          </Suspense>
        ),
      },
      {
        path: 'privacy',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <PrivacyPolicyPage />
          </Suspense>
        ),
      },
      {
        path: 'terms',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <TermsOfServicePage />
          </Suspense>
        ),
      },
      {
        path: 'refund',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <RefundPolicyPage />
          </Suspense>
        ),
      },
      // ── Shortcut routes for nav dropdown links ──────────────────────────
      {
        path: 'profile',
        element: <L component={Profile} errorBoundary />,
      },
      {
        path: 'settings',
        element: <L component={Settings} errorBoundary />,
      },
      {
        path: 'orgs',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <OrganizationsPage />
          </Suspense>
        ),
      },
      {
        path: 'orgs/:id',
        element: (
          <Suspense fallback={<PageSkeleton />}>
            <OrganizationSettingsPage />
          </Suspense>
        ),
      },
      {
        path: 'dashboard',
        element: <L component={DashboardOverview} errorBoundary />,
      },
      ...templateRoutes.map((r) => ({ ...r, errorElement: <ErrorBoundary /> })),
    ],
  },
  { path: '*', element: <NotFound /> },
]);
