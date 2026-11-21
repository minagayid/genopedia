import { Route, Routes } from 'react-router-dom';
import { RequireAuth } from '../components/auth/RequireAuth';
import { AppLayout } from '../components/layout/AppLayout';
import { LandingPage } from '../pages/landing/LandingPage';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { AnalyzePage } from '../pages/analyze/AnalyzePage';
import { AnalysisDetailPage } from '../pages/analyze/AnalysisDetailPage';
import { ComparePage } from '../pages/compare/ComparePage';
import { AiPage } from '../pages/ai/AiPage';
import { SettingsPage } from '../pages/settings/SettingsPage';
import { NotFoundPage } from '../pages/NotFoundPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/app"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="analyze" element={<AnalyzePage />} />
        <Route path="analyses/:id" element={<AnalysisDetailPage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="ai" element={<AiPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
