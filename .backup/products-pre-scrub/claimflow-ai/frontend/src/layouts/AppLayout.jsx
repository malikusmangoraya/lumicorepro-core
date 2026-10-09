import ButtonMotion from '@/components/ui/ButtonMotion';
import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, Users, Settings, Bell } from 'lucide-react';

export default function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/60 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-bold text-white">
            Console<span className="text-cyan-400">Admin</span>
          </span>
          <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-[10px] font-semibold text-cyan-400">
            Live
          </span>
        </div>
        <div className="flex items-center gap-4 text-slate-400 text-sm">
          <ButtonMotion
            type="button"
            className="p-1.5 rounded-lg hover:bg-slate-800 hover:text-white"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
          </ButtonMotion>
          <div className="flex items-center gap-2 border-l border-slate-800 pl-4">
            <div className="h-7 w-7 rounded-full bg-gradient-to-r from-cyan-500 to-violet-500 flex items-center justify-center text-xs font-bold text-slate-950">
              A
            </div>
            <span className="text-xs font-medium text-slate-200">Admin</span>
          </div>
        </div>
      </header>
      <div className="flex-1 flex">
        <aside
          className="w-56 border-r border-slate-800 bg-slate-950 p-4 space-y-1 text-xs"
          aria-label="Navigation"
        >
          <Link
            to="/"
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-900 hover:text-cyan-400"
          >
            <BarChart3 className="h-4 w-4" /> Overview
          </Link>
          <Link
            to="/services"
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-900 hover:text-cyan-400"
          >
            <Users className="h-4 w-4" /> Customers
          </Link>
          <Link
            to="/about"
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-900 hover:text-cyan-400"
          >
            <Settings className="h-4 w-4" /> Settings
          </Link>
        </aside>
        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
