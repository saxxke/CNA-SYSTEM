import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ProtectedRoute, RoleRoute } from './auth/ProtectedRoute';
import { USER_ROLES, DEFAULT_ROLE_REDIRECTS } from './auth/roleNavigation';

import AppLayout from './components/layout/AppLayout';

// Core Investigation Pages (IO & IPS)
import DashboardPage from './pages/DashboardPage';
import CasesPage from './pages/CasesPage';
import EntitiesPage from './pages/EntitiesPage';
import PersonProfilePage from './pages/PersonProfilePage';
import FamilyExplorerPage from './pages/FamilyExplorerPage';
import AdvancedSearchPage from './pages/AdvancedSearchPage';
import AssistantPage from './pages/AssistantPage';
import NetworkPage from './pages/NetworkPage';
import AnalyticsPage from './pages/AnalyticsPage';
import PriorityPage from './pages/PriorityPage';
import RegisterCasePage from './pages/RegisterCasePage';

// Phase 5 Auth & Role-Specific Pages
import LoginPage from './pages/LoginPage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import ProfilePage from './pages/ProfilePage';
import CitizenDashboardPage from './pages/citizen/CitizenDashboardPage';
import CitizenCasesPage from './pages/citizen/CitizenCasesPage';
import MinistryDashboardPage from './pages/ministry/MinistryDashboardPage';
import SupervisoryAnalyticsPage from './pages/supervisory/SupervisoryAnalyticsPage';
import AuditLogsPage from './pages/AuditLogsPage';

/**
 * Intelligent root redirect component based on backend-authenticated role.
 */
function RootRedirect() {
  const { role, isAuthenticated, loading } = useAuth();

  if (loading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const defaultDestination = (role && DEFAULT_ROLE_REDIRECTS[role]) || '/dashboard';
  return <Navigate to={defaultDestination} replace />;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Role Access Denial Page */}
            <Route path="/unauthorized" element={<UnauthorizedPage />} />

            {/* Protected Application Layout */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<RootRedirect />} />

              {/* Shared Authenticated Profile */}
              <Route path="profile" element={<ProfilePage />} />

              {/* ======================================================== */}
              {/* CITIZEN PORTAL MODULES                                   */}
              {/* Strictly limited to authenticated CITIZEN role           */}
              {/* ======================================================== */}
              <Route element={<RoleRoute allowedRoles={[USER_ROLES.CITIZEN]} />}>
                <Route path="citizen/dashboard" element={<CitizenDashboardPage />} />
                <Route path="citizen/cases" element={<CitizenCasesPage />} />
                <Route path="citizen" element={<Navigate to="/citizen/dashboard" replace />} />
              </Route>

              {/* ======================================================== */}
              {/* INVESTIGATOR MODULES (IO & IPS)                          */}
              {/* ======================================================== */}
              <Route element={<RoleRoute allowedRoles={[USER_ROLES.INVESTIGATING_OFFICER, USER_ROLES.IPS_OFFICER]} />}>
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="assistant" element={<AssistantPage />} />
                <Route path="search" element={<AdvancedSearchPage />} />
                
                {/* Case Explorer, Registration & Details */}
                <Route path="cases" element={<CasesPage />} />
                <Route path="cases/new" element={<RegisterCasePage />} />
                <Route path="cases/:caseId" element={<CasesPage />} />

                {/* Network Visualization */}
                <Route path="network" element={<NetworkPage />} />

                {/* Person Profile & Entity Directory */}
                <Route path="entities" element={<EntitiesPage />} />
                <Route path="entities/:entityId" element={<PersonProfilePage />} />
                <Route path="person/:entityId" element={<PersonProfilePage />} />

                {/* Family & Relationship Explorer */}
                <Route path="family" element={<FamilyExplorerPage />} />
                <Route path="family/:entityId" element={<FamilyExplorerPage />} />
                <Route path="entities/:entityId/family" element={<FamilyExplorerPage />} />

                {/* Graph Analytics & Prioritized Leads */}
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="priority" element={<PriorityPage />} />
              </Route>

              {/* ======================================================== */}
              {/* IPS SUPERVISORY MODULES                                  */}
              {/* Cross-case connectivity and executive reporting          */}
              {/* ======================================================== */}
              <Route element={<RoleRoute allowedRoles={[USER_ROLES.IPS_OFFICER]} />}>
                <Route path="supervisory/cross-case" element={<SupervisoryAnalyticsPage />} />
                <Route path="supervisory/reports" element={<SupervisoryAnalyticsPage />} />
                {/* Support direct legacy deep-links */}
                <Route path="analytics/cross-case" element={<SupervisoryAnalyticsPage />} />
                <Route path="analytics/reports" element={<SupervisoryAnalyticsPage />} />
              </Route>

              {/* ======================================================== */}
              {/* HOME MINISTRY STRATEGIC OVERSIGHT                        */}
              {/* Aggregated analytics, macro trends & regional statistics */}
              {/* ======================================================== */}
              <Route element={<RoleRoute allowedRoles={[USER_ROLES.HOME_MINISTRY]} />}>
                <Route path="ministry/dashboard" element={<MinistryDashboardPage />} />
                <Route path="ministry/analytics" element={<MinistryDashboardPage />} />
                <Route path="ministry/trends" element={<MinistryDashboardPage />} />
                <Route path="ministry/regional" element={<MinistryDashboardPage />} />
                <Route path="ministry/reports" element={<MinistryDashboardPage />} />
                {/* Support direct legacy deep-links */}
                <Route path="analytics/strategic-trends" element={<MinistryDashboardPage />} />
                <Route path="analytics/regional-statistics" element={<MinistryDashboardPage />} />
              </Route>

              {/* ======================================================== */}
              {/* AUDIT & COMPLIANCE LOG VIEWER                            */}
              {/* Exclusively accessible to IPS_OFFICER and HOME_MINISTRY  */}
              {/* ======================================================== */}
              <Route element={<RoleRoute allowedRoles={[USER_ROLES.IPS_OFFICER, USER_ROLES.HOME_MINISTRY]} />}>
                <Route path="audit" element={<AuditLogsPage />} />
                <Route path="audit/logs" element={<AuditLogsPage />} />
              </Route>

              {/* Catch-all fallback */}
              <Route path="*" element={<RootRedirect />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
