import { Routes, Route, Navigate } from 'react-router-dom';
import { PublicLayout } from '@/layouts/PublicLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { LandingPage } from '@/pages/LandingPage';
import { SpectatorDashboard } from '@/pages/SpectatorDashboard';
import { RegisterPage } from '@/pages/RegisterPage';
import { LoginPage } from '@/pages/LoginPage';
import { VerifyPage } from '@/pages/VerifyPage';
import { OwnerDashboard } from '@/pages/OwnerDashboard';
import { DisclaimerPage } from '@/pages/DisclaimerPage';
import { HowItWorksPage } from '@/pages/HowItWorksPage';
import { useAuthStore } from '@/store/authStore';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated()) return <Navigate to="/auth/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/watch" element={<SpectatorDashboard />} />
        <Route path="/disclaimer" element={<DisclaimerPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
      </Route>

      {/* Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/auth/register" element={<RegisterPage />} />
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/verify" element={<VerifyPage />} />
      </Route>

      {/* Protected Dashboard Routes */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<OwnerDashboard />} />
      </Route>
    </Routes>
  );
}

export default App;
