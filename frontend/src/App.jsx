import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import useAuthStore from './stores/authStore';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import RepresentativesPage from './pages/RepresentativesPage';
import ProfilePage from './pages/ProfilePage';
import WritingProfilesPage from './pages/WritingProfilesPage';
import NewLetterPage from './pages/NewLetterPage';
import LettersPage from './pages/LettersPage';
import LetterDetailPage from './pages/LetterDetailPage';
import DeliveryPage from './pages/DeliveryPage';
import TermsOfServicePage from './pages/TermsOfServicePage';
import PrivacyPolicyPage from './pages/PrivacyPolicyPage';

// Components
import PrivateRoute from './components/PrivateRoute';
import Layout from './components/Layout';

function App() {
  const loadUser = useAuthStore((state) => state.loadUser);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/terms" element={<TermsOfServicePage />} />
        <Route path="/privacy" element={<PrivacyPolicyPage />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="representatives" element={<RepresentativesPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="writing-profiles" element={<WritingProfilesPage />} />
          <Route path="letters/new" element={<NewLetterPage />} />
          <Route path="letters" element={<LettersPage />} />
          <Route path="letters/:id" element={<LetterDetailPage />} />
          <Route path="letters/:id/delivery" element={<DeliveryPage />} />
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
