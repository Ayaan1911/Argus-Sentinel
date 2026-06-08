import React from 'react';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-surface border-b border-bordercolor flex items-center px-6 shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-accent font-bold text-xl tracking-wider uppercase">Argus Sentinel</h1>
            <span className="text-textmut text-sm hidden sm:inline">| AI Cybersecurity Reasoning Engine</span>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
