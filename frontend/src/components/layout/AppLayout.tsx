import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Dna, FlaskConical, GitCompareArrows, LayoutDashboard, LogOut, Settings, Sparkles } from 'lucide-react';
import { logout } from '../../api';
import { useAuth } from '../../auth/AuthContext';
import { paths } from '../../routes/paths';
import { cn } from '../../lib/utils';

const nav = [
  { to: paths.dashboard, label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: paths.analyze, label: 'New analysis', icon: FlaskConical },
  { to: paths.compare, label: 'Compare', icon: GitCompareArrows },
  { to: paths.ai, label: 'AI assistant', icon: Sparkles },
  { to: paths.settings, label: 'Settings', icon: Settings },
];

export function AppLayout() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  async function handleLogout() {
    await logout();
    setUser(null);
    navigate('/');
  }
  return (
    <div className="flex min-h-screen bg-slate-950 bg-mesh-dark">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-800 bg-slate-950/80 p-4 md:flex">
        <NavLink to="/" className="mb-8 flex items-center gap-2 px-2 pt-2">
          <Dna className="h-6 w-6 text-brand-400" />
          <span className="text-lg font-bold text-gradient">Genopedia</span>
        </NavLink>
        <nav className="flex flex-1 flex-col gap-1">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive ? 'bg-brand-500/10 text-brand-300' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 pt-4">
          <p className="truncate px-2 text-xs text-slate-500">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-4 md:p-8">
        <MobileNav />
        <Outlet />
      </main>
    </div>
  );
}

function MobileNav() {
  return (
    <nav className="mb-6 flex gap-1 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 p-1.5 md:hidden">
      {nav.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              'flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium',
              isActive ? 'bg-brand-500/10 text-brand-300' : 'text-slate-400',
            )
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
