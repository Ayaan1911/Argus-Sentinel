import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { LayoutDashboard, Target, BookOpen } from 'lucide-react';

export default function Sidebar() {
  const links = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'New Scan', path: '/scan/new', icon: <Target size={20} /> },
    { name: 'Intelligence Library', path: '/intelligence', icon: <BookOpen size={20} /> },
  ];

  return (
    <div className="w-16 md:w-60 bg-surface/70 backdrop-blur-xl border-r border-bordercolor flex flex-col justify-between shrink-0 h-full transition-all">
      <div className="p-2 md:p-4">
        {/* Persistent way back to the public landing page — a real link, not
            decorative branding, with its own hover state so it reads as
            clickable rather than just a logo mark. */}
        <Link
          to="/"
          title="Back to landing page"
          className="mb-8 px-1 md:px-2 pt-2 flex items-center gap-2 group"
        >
          <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center shrink-0 shadow-glow-accent group-hover:bg-accent/30 transition-colors">
            <span className="text-accent font-black text-xl">A</span>
          </div>
          <span className="hidden md:inline text-textpri font-black tracking-[0.18em] text-sm group-hover:text-accent transition-colors">SENTINEL</span>
        </Link>
        <nav className="space-y-2">
          {links.map((link) => (
            <NavLink
              key={link.name}
              to={link.path}
              title={link.name}
              className={({ isActive }) =>
                `flex items-center justify-center md:justify-start gap-3 px-3 py-2 rounded-md transition-colors ${
                  isActive
                    ? 'bg-accent/15 text-accent font-bold shadow-glow-accent'
                    : 'text-textmut hover:bg-card hover:text-textpri'
                }`
              }
            >
              {link.icon}
              <span className="hidden md:inline">{link.name}</span>
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="p-2 md:p-4 border-t border-bordercolor flex justify-center md:justify-start">
        <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono bg-card text-textmut border border-bordercolor">
          <span className="hidden md:inline">v1.0.0</span>
          <span className="md:hidden">v1</span>
        </div>
      </div>
    </div>
  );
}
