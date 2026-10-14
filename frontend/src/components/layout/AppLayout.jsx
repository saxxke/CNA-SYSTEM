import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import SafetyBanner from './SafetyBanner';

export default function AppLayout() {
  const location = useLocation();
  // Network page needs its own internal full-height canvas without outer page scroll
  const isNetwork = location.pathname.startsWith('/network');

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100">
      <SafetyBanner />
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        {isNetwork ? (
          <main className="flex-1 overflow-hidden relative flex flex-col bg-slate-950">
            <Outlet />
          </main>
        ) : (
          <main className="flex-1 overflow-y-auto relative bg-slate-950 flex flex-col justify-between">
            <div>
              <Outlet />
            </div>
            <footer className="mt-12 border-t border-slate-800/80 py-4 px-6 text-center text-[11px] text-slate-400 bg-slate-950/80">
              Investigation Network Analysis & Evidence Intelligence Platform • AI Decision Support System • All analytical leads require human verification.
            </footer>
          </main>
        )}
      </div>
    </div>
  );
}
