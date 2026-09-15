import React from 'react';
import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';
import { GITHUB_URL } from './data';

export default function Nav() {
  return (
    <header className="sticky top-0 z-20 backdrop-blur-xl bg-background/70 border-b border-white/[0.06]">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center shadow-glow-accent">
            <span className="text-accent font-black text-xl">A</span>
          </div>
          <span className="text-textpri font-black tracking-[0.18em] text-sm">SENTINEL</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-sm text-textmut hover:text-textpri transition-colors hidden sm:inline">
            Launch App
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-sm font-semibold text-textpri border border-bordercolor hover:border-accent/50 rounded-md px-3 py-1.5 transition-colors"
          >
            <Github size={16} /> GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
