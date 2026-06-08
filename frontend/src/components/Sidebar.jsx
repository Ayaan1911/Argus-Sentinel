import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Target, BookOpen } from 'lucide-react';

export default function Sidebar() {
  const links = [
    { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
    { name: 'New Scan', path: '/scan/new', icon: <Target size={20} /> },
    { name: 'Intelligence Library', path: '/intelligence', icon: <BookOpen size={20} /> },
  ];

  return (
    <div className="w-60 bg-surface border-r border-bordercolor flex flex-col justify-between shrink-0 h-full">
      <div className="p-4">
        <div className="mb-8 px-2 pt-2">
          <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center mb-2">
            <span className="text-accent font-bold text-xl">A</span>
          </div>
        </div>
        <nav className="space-y-2">
          {links.map((link) => (
            <NavLink
              key={link.name}
              to={link.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                  isActive 
                    ? 'bg-accent/10 text-accent font-medium' 
                    : 'text-textmut hover:bg-card hover:text-textpri'
                }`
              }
            >
              {link.icon}
              {link.name}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="p-4 border-t border-bordercolor">
        <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono bg-card text-textmut border border-bordercolor">
          v1.0.0
        </div>
      </div>
    </div>
  );
}
