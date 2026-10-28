import { Route, Routes } from 'react-router-dom';
import SiteLayout from './components/SiteLayout.jsx';
import AboutPage from './pages/AboutPage.jsx';
import AccountPage from './pages/AccountPage.jsx';
import AuthPage from './pages/AuthPage.jsx';
import ContactPage from './pages/ContactPage.jsx';
import HomePage from './pages/HomePage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import PolicyPages from './pages/PolicyPages.jsx';
import PricingPage from './pages/PricingPage.jsx';
import ServicesPage from './pages/ServicesPage.jsx';
import UnavailablePage from './pages/UnavailablePage.jsx';

function App() {
  return (
    <Routes>
      <Route element={<SiteLayout />}>
        <Route index element={<HomePage />} />
        <Route path="services" element={<ServicesPage />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="contact" element={<ContactPage />} />
        <Route path="privacy" element={<PolicyPages page="privacy" />} />
        <Route path="terms" element={<PolicyPages page="terms" />} />
        <Route path="login" element={<AuthPage mode="login" />} />
        <Route path="register" element={<AuthPage mode="register" />} />
        <Route path="reset-password" element={<AuthPage mode="reset" />} />
        <Route path="account" element={<AccountPage />} />
        <Route path="admin" element={<UnavailablePage route="admin" />} />
        <Route path="checkout" element={<UnavailablePage route="checkout" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
