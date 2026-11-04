import React, { useEffect, useState } from 'react';
import { clearAuthSession } from '../auth.js';
import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom';
import { PenTool, History as HistoryIcon, Coins, LogOut, Feather } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

const NAV = [
  { to: '/generate', label: 'Generate', icon: PenTool, end: true },
  { to: '/generate/history', label: 'History', icon: HistoryIcon, end: false },
  { to: '/generate/credits', label: 'Credits', icon: Coins, end: false },
];

export default function WorkspaceLayout() {
  const navigate = useNavigate();
  const [balance, setBalance] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return navigate(`/login?next=${encodeURIComponent(window.location.pathname)}`, { replace: true });
    try { setUser(JSON.parse(localStorage.getItem('user') || 'null')); } catch { /* ignore */ }
    fetch(`${API}/blog/credits`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => {
        if (r.status === 401) {
          clearAuthSession();
          navigate(`/login?next=${encodeURIComponent(window.location.pathname)}`, { replace: true });
          return null;
        }
        return r.ok ? r.json() : null;
      })
      .then((j) => { if (j?.success) setBalance(j.data.balance); })
      .catch(() => {});
  }, [navigate]);

  const logout = () => {
    clearAuthSession();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="hidden md:flex w-64 flex-col border-r border-slate-800 bg-slate-900/60 backdrop-blur p-5 gap-8" aria-label="Workspace navigation">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg">
          <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 grid place-items-center">
            <Feather className="w-5 h-5 text-white" />
          </span>
          Blog<span className="bg-gradient-to-r from-indigo-400 to-fuchsia-400 bg-clip-text text-transparent">Forge</span>
        </Link>
        <nav className="flex flex-col gap-1" aria-label="Primary">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-500/20 to-fuchsia-500/10 text-white border border-indigo-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-3">
          <div className="px-3 py-3 rounded-xl bg-slate-800/60 border border-slate-700/60">
            <p className="text-xs text-slate-400">Credit balance</p>
            <p className="text-2xl font-bold tabular-nums bg-gradient-to-r from-indigo-400 to-fuchsia-400 bg-clip-text text-transparent" data-testid="sidebar-balance">{balance ?? '—'}</p>
          </div>
          {user && <p className="px-3 text-xs text-slate-500 truncate">{user.email}</p>}
          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-white rounded-xl hover:bg-slate-800/60 transition-all duration-200"
          >
            <LogOut className="w-4 h-4" /> Log out
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="md:hidden sticky top-0 z-40 border-b border-slate-800 bg-slate-950/90 backdrop-blur px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <Link to="/" className="flex items-center gap-2 font-bold text-base">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-fuchsia-500 grid place-items-center">
                <Feather className="w-4 h-4 text-white" />
              </span>
              Blog<span className="bg-gradient-to-r from-indigo-400 to-fuchsia-400 bg-clip-text text-transparent">Forge</span>
            </Link>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-semibold tabular-nums" data-testid="mobile-balance">
                <span className="text-slate-400">Credits</span> {balance ?? '—'}
              </span>
              <button
                type="button"
                onClick={logout}
                aria-label="Log out"
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
          <nav className="mt-3 grid grid-cols-3 gap-2" aria-label="Workspace">
            {NAV.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    isActive ? 'bg-indigo-500/20 text-white border border-indigo-500/30' : 'text-slate-400 hover:text-white bg-slate-900 border border-slate-800'
                  }`
                }
              >
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
          </nav>
        </header>

        <Outlet context={{ balance, setBalance }} />
      </div>
    </div>
  );
}
