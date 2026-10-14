import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { Loader2, Shield } from 'lucide-react';

/**
 * Ensures user is authenticated.
 * Unauthenticated requests are redirected to /login with state.from preserved.
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300">
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 px-6 py-4 rounded-xl shadow-2xl backdrop-blur-md">
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
          <span className="text-xs font-semibold tracking-wide">Verifying Session Security…</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? children : <Outlet />;
}

/**
 * Ensures authenticated user possesses an allowed role.
 * Unauthorized roles are redirected to /unauthorized without leaking sensitive UI.
 */
export function RoleRoute({ allowedRoles = [], children }) {
  const { role, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300">
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 px-6 py-4 rounded-xl shadow-2xl backdrop-blur-md">
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
          <span className="text-xs font-semibold tracking-wide">Checking Role Authorization…</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!allowedRoles.includes(role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children ? children : <Outlet />;
}

export default ProtectedRoute;
