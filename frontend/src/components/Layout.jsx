import React from 'react';
import Sidebar from './Sidebar';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-surface/70 backdrop-blur-xl border-b border-bordercolor flex items-center px-4 sm:px-6 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="text-accent font-bold text-lg sm:text-xl tracking-wider uppercase truncate">Argus Sentinel</h1>
            <span className="text-textmut text-sm hidden lg:inline shrink-0">| AI Cybersecurity Reasoning Engine</span>
          </div>
        </header>
        {DEMO_MODE && (
          <div className="bg-warning/10 border-b border-warning/30 text-warning text-sm px-6 py-2 text-center shrink-0">
            You're viewing the public demo — scans are locked to a bundled vulnerable test app.{' '}
            <a
              href="https://github.com/Ayaan1911/Argus-Sentinel#readme"
              target="_blank"
              rel="noreferrer"
              className="underline font-semibold hover:text-textpri"
            >
              Self-host to scan your own targets.
            </a>
          </div>
        )}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
